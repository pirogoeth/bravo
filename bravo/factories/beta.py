from collections import defaultdict
from itertools import chain
from time import time

from twisted.internet.interfaces import IPushProducer
from twisted.internet.protocol import Factory
from twisted.internet.task import LoopingCall
from twisted.python import log
from zope.interface import implements

from bravo.config import configuration
from bravo.entity import entities
from bravo.ibravo import (ISortedPlugin, IAutomaton, IAuthenticator, ISeason,
    ITerrainGenerator, IUseHook, ISignHook, IDigHook, IPreBuildHook,
    IPostBuildHook)
from bravo.location import Location
from bravo.packets.beta import make_packet
from bravo.plugin import retrieve_named_plugins, retrieve_sorted_plugins
from bravo.protocols.beta import BannedProtocol, BravoProtocol
from bravo.utilities.chat import chat_name, sanitize_chat
from bravo.world import World

(STATE_UNAUTHENTICATED, STATE_CHALLENGED, STATE_AUTHENTICATED,
    STATE_LOCATED) = range(4)

class BravoFactory(Factory):
    """
    A ``Factory`` that creates ``BravoProtocol`` objects when connected to.
    """

    implements(IPushProducer)

    protocol = BravoProtocol

    timestamp = None
    time = 0
    day = 0
    eid = 1

    handshake_hook = None
    login_hook = None

    interface = ""

    def __init__(self, name):
        """
        Create a factory and world.

        ``name`` is the string used to look up factory-specific settings from
        the configuration.

        :param str name: internal name of this factory
        """

        self.name = name
        self.config_name = "world %s" % name

        self.port = configuration.getint(self.config_name, "port")
        self.interface = configuration.getdefault(self.config_name, "host",
            "")

        self.world = World(self.name)
        self.world.factory = self

        self.protocols = dict()

    def startFactory(self):
        log.msg("Initializing factory for world '%s'..." % self.name)

        authenticator = configuration.get(self.config_name, "authenticator")
        selected = retrieve_named_plugins(IAuthenticator, [authenticator])[0]

        log.msg("Using authenticator %s" % selected.name)
        self.handshake_hook = selected.handshake
        self.login_hook = selected.login

        # Get our plugins set up.
        self.register_plugins()

        log.msg("Starting world...")
        self.world.start()

        if configuration.has_option(self.config_name, "perm_cache"):
            cache_level = configuration.getint(self.config_name, "perm_cache")
            self.world.enable_cache(cache_level)

        log.msg("Starting timekeeping...")
        self.timestamp = time()
        self.time = self.world.time
        self.update_season()
        self.time_loop = LoopingCall(self.update_time)
        self.time_loop.start(2)

        # Start automatons.
        for automaton in self.automatons:
            automaton.start()

        self.chat_consumers = set()

        log.msg("Factory successfully initialized for world '%s'!" % self.name)

    def stopFactory(self):
        """
        Called before factory stops listening on ports. Used to perform
        shutdown tasks.
        """

        log.msg("Shutting down world...")

        # Stop automatons. Technically, they may not actually halt until their
        # next iteration, but that is close enough for us, probably.
        # Automatons are contracted to not access the world after stop() is
        # called.
        for automaton in self.automatons:
            automaton.stop()

        self.time_loop.stop()

        # Write back current world time. This must be done before stopping the
        # world.
        self.world.time = self.time

        # And now stop the world.
        self.world.stop()

        log.msg("World data saved!")

    def buildProtocol(self, addr):
        """
        Create a protocol.

        This overriden method provides early player entity registration, as a
        solution to the username/entity race that occurs on login.
        """

        banned = self.world.serializer.load_plugin_data("banned_ips")

        for ip in banned.split():
            if addr.host == ip:
                # Use BannedProtocol with extreme prejudice.
                log.msg("Kicking banned IP %s" % addr)
                p = BannedProtocol()
                p.factory = self
                return p

        log.msg("Starting connection for %s" % addr)
        p = self.protocol(self.name)
        p.factory = self

        self.register_entity(p)

        # Copy our hooks to the protocol.
        p.register_hooks()

        return p

    def set_username(self, protocol, username):
        """
        Attempt to set a new username for a protocol.

        :returns: whether the username was changed
        """

        # If the username's already taken, refuse it.
        if username in self.protocols:
            return False

        if protocol.username in self.protocols:
            # This protocol's known under another name, so remove it.
            del self.protocols[protocol.username]

        # Set the username.
        self.protocols[username] = protocol
        protocol.username = username

        return True

    def register_plugins(self):
        """
        Setup plugin hooks.
        """

        log.msg("Registering client plugin hooks...")

        plugin_types = {
            "automatons": IAutomaton,
            "generators": ITerrainGenerator,
            "seasons": ISeason,
            "pre_build_hooks": IPreBuildHook,
            "post_build_hooks": IPostBuildHook,
            "dig_hooks": IDigHook,
            "sign_hooks": ISignHook,
            "use_hooks": IUseHook,
        }

        pp = {"factory": self}

        for t, interface in plugin_types.iteritems():
            l = configuration.getlistdefault(self.config_name, t, [])
            if issubclass(interface, ISortedPlugin):
                plugins = retrieve_sorted_plugins(interface, l, parameters=pp)
            else:
                plugins = retrieve_named_plugins(interface, l, parameters=pp)
            log.msg("Using %s: %s" % (t.replace("_", " "),
                ", ".join(plugin.name for plugin in plugins)))
            setattr(self, t, plugins)

        # Assign generators to the world pipeline.
        self.world.pipeline = self.generators

        # Use hooks have special funkiness.
        uh = self.use_hooks
        self.use_hooks = defaultdict(list)
        for plugin in uh:
            for target in plugin.targets:
                self.use_hooks[target].append(plugin)

    def create_entity(self, x, y, z, name, **kwargs):
        """
        Spawn an entirely new entity.

        Handles entity registration as well as instantiation.
        """

        location = Location()
        location.x = x
        location.y = y
        location.z = z
        entity = entities[name](eid=0, location=location, **kwargs)

        self.register_entity(entity)

        bigx = entity.location.x // 16
        bigz = entity.location.z // 16

        d = self.world.request_chunk(bigx, bigz)
        d.addCallback(lambda chunk: chunk.entities.add(entity))
        d.addCallback(lambda none: log.msg("Created entity %s" % entity))

        return entity

    def register_entity(self, entity):
        """
        Registers an entity with this factory.

        Registration is perhaps too fancy of a name; this method merely makes
        sure that the entity has a unique and usable entity ID.
        """

        if not entity.eid:
            self.eid += 1
            entity.eid = self.eid

        log.msg("Registered entity %s" % entity)

    def destroy_entity(self, entity):
        """
        Destroy an entity.

        The factory doesn't have to know about entities, but it is a good
        place to put this logic.
        """

        bigx = entity.location.x // 16
        bigz = entity.location.z // 16

        d = self.world.request_chunk(bigx, bigz)
        d.addCallback(lambda chunk: chunk.entities.discard(entity))
        d.addCallback(lambda none: log.msg("Destroyed entity %s" % entity))

    def update_time(self):
        """
        Update the in-game timer.

        The timer goes from 0 to 24000, both of which are high noon. The clock
        increments by 20 every second. Days are 20 minutes long.

        The day clock is incremented every in-game day, which is every 20
        minutes. The day clock goes from 0 to 360, which works out to a reset
        once every 5 days. This is a Babylonian in-game year.
        """

        t = time()
        self.time += 20 * (t - self.timestamp)
        self.timestamp = t

        while self.time > 24000:
            self.time -= 24000

            self.day += 1
            while self.day > 360:
                self.day -= 360

            self.update_season()

    def broadcast_time(self):
        packet = make_packet("time", timestamp=int(self.time))
        self.broadcast(packet)

    def update_season(self):
        """
        Update the world's season.
        """

        all_seasons = sorted(self.seasons, key=lambda s: s.day)

        # Get all the seasons that we have past the start date of this year.
        # We are looking for the season which is closest to our current day,
        # without going over; I call this the Price-is-Right style of season
        # handling. :3
        past_seasons = [s for s in all_seasons if s.day <= self.day]
        if past_seasons:
            # The most recent one is the one we are in
            self.world.season = past_seasons[-1]
        elif all_seasons:
            # We haven't past any seasons yet this year, so grab the last one
            # from 'last year'
            self.world.season = all_seasons[-1]
        else:
            # No seasons enabled.
            self.world.season = None

    def chat(self, message):
        """
        Relay chat messages.

        Chat messages are sent to all connected clients, as well as to anybody
        consuming this factory.
        """

        for consumer in self.chat_consumers:
            consumer.write((self, message))

        # Prepare the message for chat packeting.
        for user in self.protocols:
            message = message.replace(user, chat_name(user))
        message = sanitize_chat(message)

        log.msg("Chat: %s" % message.encode("utf8"))

        packet = make_packet("chat", message=message)
        self.broadcast(packet)

    def broadcast(self, packet):
        """
        Broadcast a packet to all connected players.
        """

        for player in self.protocols.itervalues():
            player.transport.write(packet)

    def broadcast_for_others(self, packet, protocol):
        """
        Broadcast a packet to all players except the originating player.

        Useful for certain packets like player entity spawns which should
        never be reflexive.
        """

        for player in self.protocols.itervalues():
            if player is not protocol:
                player.transport.write(packet)

    def broadcast_for_chunk(self, packet, x, z):
        """
        Broadcast a packet to all players that have a certain chunk loaded.

        `x` and `z` are chunk coordinates, not block coordinates.
        """

        for player in self.protocols.itervalues():
            if (x, z) in player.chunks:
                player.transport.write(packet)

    def scan_chunk(self, chunk):
        """
        Tell automatons about this chunk.
        """

        for automaton in self.automatons:
            automaton.scan(chunk)

    def flush_chunk(self, chunk):
        """
        Flush a damaged chunk to all players that have it loaded.
        """

        if chunk.is_damaged():
            packet = chunk.get_damage_packet()
            for player in self.protocols.itervalues():
                if (chunk.x, chunk.z) in player.chunks:
                    player.transport.write(packet)
            chunk.clear_damage()

    def flush_all_chunks(self):
        """
        Flush any damage anywhere in this world to all players.

        This is a sledgehammer which should be used sparingly at best, and is
        only well-suited to plugins which touch multiple chunks at once.

        In other words, if I catch you using this in your plugin needlessly,
        I'm gonna have a chat with you.
        """

        for chunk in chain(self.world.chunk_cache.itervalues(),
            self.world.dirty_chunk_cache.itervalues()):
            self.flush_chunk(chunk)

    def give(self, coords, block, quantity):
        """
        Spawn a pickup at the specified coordinates.

        The coordinates need to be in pixels, not blocks.

        If the size of the stack is too big, multiple stacks will be dropped.

        :param tuple coords: coordinates, in pixels
        :param tuple block: key of block or item to drop
        :param int quantity: number of blocks to drop in the stack
        """

        x, y, z = coords

        while quantity > 0:
            entity = self.create_entity(x // 32, y // 32, z // 32, "Item",
                item=block, quantity=min(quantity, 64))

            packet = entity.save_to_packet()
            packet += make_packet("create", eid=entity.eid)
            self.broadcast(packet)

            quantity -= 64

    def players_near(self, player, radius):
        """
        Obtain other players within a radius of a given player.

        Radius is measured in blocks.
        """

        for i in (p for p in self.protocols.itervalues()
            if player.location.distance(p.location) <= radius and
            p.player != player):
            yield i.player

    def pauseProducing(self):
        pass

    def resumeProducing(self):
        pass

    def stopProducing(self):
        pass
