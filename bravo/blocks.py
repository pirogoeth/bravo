from __future__ import division

faces = ("-y", "+y", "-z", "+z", "-x", "+x")

class Block(object):
    """
    A model for a block.

    There are lots of rule and properties specific to different types of
    blocks. This class encapsulates those properties in a singleton-style
    interface, allowing many blocks to be referenced in one location.

    The basic idea of this class is to provide some centralized data and
    information about blocks, in order to abstract away as many special cases
    as possible. In general, if several blocks all have some special behavior,
    then it may be worthwhile to store data describing that behavior on this
    class rather than special-casing it in multiple places.
    """

    __slots__ = (
        "_o_dict",
        "breakable",
        "dim",
        "drop",
        "key",
        "name",
        "quantity",
        "ratio",
        "replace",
        "slot",
    )

    def __init__(self, slot, name, secondary=0, drop=None, replace=0, ratio=1,
        quantity=1, dim=16, breakable=True, orientation=None):
        """
        :param int slot: The index of this block. Must be globally unique.
        :param str name: A common name for this block.
        :param int secondary: The metadata/damage/secondary attribute for this
            block. Defaults to zero.
        :param int drop: The type of block that should be dropped when an
            instance of this block is destroyed. Defaults to the slot value, to
            drop instances of this same type of block. To indicate that this
            block does not drop anything, set to air.
        :param int replace: The type of block to place in the map when
            instances of this block are destroyed. Defaults to air.
        :param float ratio: The probability of this block dropping a block
            on destruction.
        :param int quantity: The number of blocks dropped when this block
            is destroyed.
        :param int dim: How much light dims when passing through this kind
            of block. Defaults to 16 = opaque block.
        :param bool breakable: Whether this block is diggable, breakable,
            bombable, explodeable, etc. Only a few blocks actually genuinely
            cannot be broken, so the default is True.
        :param tuple orientation: The orientation data for a block. See
            :meth:`orientable` for an explanation. The data should be in standard
            face order.
        """

        self.slot = slot
        self.name = name

        self.key = (self.slot, secondary)

        if drop is None:
            self.drop = slot
        else:
            self.drop = drop

        self.replace = replace
        self.ratio = ratio
        self.quantity = quantity
        self.dim = dim
        self.breakable = breakable

        if orientation:
            self._o_dict = dict(zip(faces, orientation))
        else:
            self._o_dict = {}

    def __str__(self):
        """
        Fairly verbose explanation of what this block is capable of.
        """

        attributes = []
        if not self.breakable:
            attributes.append("unbreakable")
        if self.dim == 0:
            attributes.append("transparent")
        elif self.dim < 16:
            attributes.append("translucent (%d)" % self.dim)
        if self.replace:
            attributes.append("becomes %d" % self.replace)
        if self.ratio != 1 or self.quantity > 1 or self.drop != self.slot:
            attributes.append("drops %d slot %d rate %2.2f%%" %
                (self.quantity, self.drop, self.ratio * 100))
        if attributes:
            attributes = ": %s" % ", ".join(attributes)
        else:
            attributes = ""

        return "Block(%r %r%s)" % (self.key, self.name, attributes)

    __repr__ = __str__

    def orientable(self):
        """
        Whether this block can be oriented.

        Orientable blocks are positioned according to the face on which they
        are built. They may not be buildable on all faces. Blocks are only
        orientable if their metadata can be used to directly and uniquely
        determine the face against which they were built.

        Ladders are orientable, signposts are not.

        :rtype: bool
        :returns: True if this block can be oriented, False if not.
        """

        return any(self._o_dict)

    def orientation(self, face):
        """
        Retrieve the metadata for a certain orientation, or None if this block
        cannot be built against the given face.

        This method only returns valid data for orientable blocks; check
        :meth:`orientable` first.
        """

        return self._o_dict.get(face)

class Item(object):
    """
    An item.
    """

    __slots__ = (
        "key",
        "name",
        "slot",
    )

    def __init__(self, slot, name, secondary=0):

        self.slot = slot
        self.name = name

        self.key = (self.slot, secondary)

    def __str__(self):
        return "Item(%r %r)" % (self.key, self.name)

    __repr__ = __str__

block_names = [
    "air", # 0x0
    "stone",
    "grass",
    "dirt",
    "cobblestone",
    "wood",
    "sapling",
    "bedrock",
    "water",
    "spring",
    "lava",
    "lava-spring",
    "sand",
    "gravel",
    "gold-ore",
    "iron-ore",
    "coal-ore", # 0x10
    "log",
    "leaves",
    "sponge",
    "glass",
    "lapis-lazuli-ore",
    "lapis-lazuli",
    "dispenser",
    "sandstone",
    "note-block",
    "bed",
    "powered-rail",
    "detector-rail",
    "",
    "spider-web",
    "",
    "", # 0x20
    "",
    "",
    "wool",
    "",
    "flower",
    "rose",
    "brown-mushroom",
    "red-mushroom",
    "gold",
    "iron",
    "double-step",
    "step",
    "brick",
    "tnt",
    "bookshelf",
    "mossy-cobblestone", # 0x30
    "obsidian",
    "torch",
    "fire",
    "mob-spawner",
    "wooden-stairs",
    "chest",
    "redstone-wire",
    "diamond-ore",
    "diamond",
    "workbench",
    "crops",
    "soil",
    "furnace",
    "burning-furnace",
    "signpost",
    "wooden-door", # 0x40
    "ladder",
    "tracks",
    "stone-stairs",
    "wall-sign",
    "lever",
    "stone-plate",
    "iron-door",
    "wooden-plate",
    "redstone-ore",
    "glowing-redstone-ore",
    "redstone-torch-off",
    "redstone-torch",
    "stone-button",
    "snow",
    "ice",
    "snow-block", # 0x50
    "cactus",
    "clay",
    "sugar-cane",
    "jukebox",
    "fence",
    "pumpkin",
    "brimstone",
    "slow-sand",
    "lightstone",
    "portal",
    "jack-o-lantern",
    "cake",
    "redstone-repeater-off",
    "redstone-repeater-on",
    "locked-chest",
]

item_names = [
    "iron-shovel",
    "iron-pickaxe",
    "iron-axe",
    "flint-and-steel",
    "apple",
    "bow",
    "arrow",
    "coal",
    "diamond",
    "iron-ingot",
    "gold-ingot",
    "iron-sword",
    "wooden-sword",
    "wooden-shovel",
    "wooden-pickaxe",
    "wooden-axe",
    "stone-sword",
    "stone-shovel",
    "stone-pickaxe",
    "stone-axe",
    "diamond-sword",
    "diamond-shovel",
    "diamond-pickaxe",
    "diamond-axe",
    "stick",
    "bowl",
    "mushroom-soup",
    "gold-sword",
    "gold-shovel",
    "gold-pickaxe",
    "gold-axe",
    "string",
    "feather",
    "sulphur",
    "wooden-hoe",
    "stone-hoe",
    "iron-hoe",
    "diamond-hoe",
    "gold-hoe",
    "seeds",
    "wheat",
    "bread",
    "leather-helmet",
    "leather-chestplate",
    "leather-leggings",
    "leather-boots",
    "chainmail-helmet",
    "chainmail-chestplate",
    "chainmail-leggings",
    "chainmail-boots",
    "iron-helmet",
    "iron-chestplate",
    "iron-leggings",
    "iron-boots",
    "diamond-helmet",
    "diamond-chestplate",
    "diamond-leggings",
    "diamond-boots",
    "gold-helmet",
    "gold-chestplate",
    "gold-leggings",
    "gold-boots",
    "flint",
    "raw-porkchop",
    "cooked-porkchop",
    "paintings",
    "golden-apple",
    "sign",
    "wooden-door",
    "bucket",
    "water-bucket",
    "lava-bucket",
    "mine-cart",
    "saddle",
    "iron-door",
    "redstone",
    "snowball",
    "boat",
    "leather",
    "milk",
    "clay-brick",
    "clay-balls",
    "sugar-cane",
    "paper",
    "book",
    "slimeball",
    "storage-minecart",
    "powered-minecart",
    "egg",
    "compass",
    "fishing-rod",
    "clock",
    "glowstone-dust",
    "raw-fish",
    "cooked-fish",
    "dye",
    "bone",
    "sugar",
    "cake",
    "bed",
    "redstone-repeater",
    "cookie",
]

special_item_names = [
    "gold-music-disc",
    "green-music-disc",
]

dye_names = [
    "ink-sac",
    "red-dye",
    "green-dye",
    "cocoa-beans",
    "lapis-lazuli",
    "purple-dye",
    "cyan-dye",
    "light-gray-dye",
    "gray-dye",
    "pink-dye",
    "lime-dye",
    "yellow-dye",
    "light-blue-dye",
    "magenta-dye",
    "orange-dye",
    "bone-meal",
]

wool_names = [
    "white-wool",
    "orange-wool",
    "magenta-wool",
    "light-blue-wool",
    "yellow-wool",
    "light-green-wool",
    "pink-wool",
    "gray-wool",
    "light-gray-wool",
    "cyan-wool",
    "purple-wool",
    "blue-wool",
    "brown-wool",
    "dark-green-wool",
    "red-wool",
    "black-wool",
]

sapling_names = [
    "normal-sapling",
    "pine-sapling",
    "birch-sapling",
]

log_names = [
    "normal-log",
    "pine-log",
    "birch-log",
]

leave_names = [
    "normal-leave",
    "pine-leave",
    "birch-leave",
]

coal_names = [
    "normal-coal",
    "charcoal",
]

step_names = [
    "stone-step",
    "sandstone-step",
    "wooden-step",
    "cobblestone-step",
]

drops = {}

# Block -> block drops.
# If the drop block is zero, then it drops nothing.
drops[1]  = 4   # Stone           -> Cobblestone
drops[2]  = 3   # Grass           -> Dirt
drops[20] = 0   # Glass
drops[52] = 0   # Mob spawner
drops[60] = 3   # Soil            -> Dirt
drops[62] = 61  # Burning Furnace -> Furnace
drops[78] = 0   # Snow

# Block -> item drops.
drops[16] = 263 # Coal Ore Block    -> Coal
drops[26] = 355 # Bed block         -> Bed
drops[56] = 264 # Diamond Ore Block -> Diamond
drops[63] = 323 # Sign Post         -> Sign Item
drops[64] = 324 # Wooden Door       -> Wooden Door Item
drops[68] = 323 # Wall Sign         -> Sign Item
drops[71] = 330 # Iron Door         -> Iron Door Item
drops[83] = 338 # Reed              -> Reed Item
drops[89] = 348 # Lightstone        -> Lightstone Dust
drops[93] = 356 # Redstone-repeater-on  -> Redstone-repeater
drops[94] = 356 # Redstone-repeater-off -> Redstone-repeater


unbreakables = set()

unbreakables.add(0)  # Air
unbreakables.add(7)  # Bedrock
unbreakables.add(10) # Lava
unbreakables.add(11) # Lava spring

dims = {}

dims[0]  = 0 # Air
dims[6]  = 0 # Sapling
dims[10] = 0 # Lava
dims[11] = 0 # Lava spring
dims[20] = 0 # Glass
dims[26] = 0 # Bed
dims[37] = 0 # Yellow Flowers
dims[38] = 0 # Red Flowers
dims[39] = 0 # Brown Mushrooms
dims[40] = 0 # Red Mushrooms
dims[44] = 0 # Single Step
dims[51] = 0 # Fire
dims[52] = 0 # Mob spawner
dims[53] = 0 # Wooden stairs
dims[55] = 0 # Redstone (Wire)
dims[59] = 0 # Crops
dims[60] = 0 # Soil
dims[63] = 0 # Sign
dims[64] = 0 # Wood door
dims[66] = 0 # Rails
dims[67] = 0 # Stone stairs
dims[68] = 0 # Sign (on wall)
dims[69] = 0 # Lever
dims[70] = 0 # Stone Pressure Plate
dims[71] = 0 # Iron door
dims[72] = 0 # Wood Pressure Plate
dims[78] = 0 # Snow
dims[81] = 0 # Cactus
dims[83] = 0 # Sugar Cane
dims[85] = 0 # Fence
dims[90] = 0 # Portal
dims[92] = 0 # Cake
dims[93] = 0 # redstone-repeater-off
dims[94] = 0 # redstone-repeater-on


blocks = {}
"""
A dictionary of ``Block`` objects.

This dictionary can be indexed by slot number or block name.
"""

def _add_block(block):
    blocks[block.slot] = block
    blocks[block.name] = block

# Special blocks. Please remember to comment *what* makes the block special;
# most of us don't have all blocks memorized yet.

# Water (both kinds) is unbreakable, and dims by 3.
_add_block(Block(8, "water", breakable=False, dim=3))
_add_block(Block(9, "spring", breakable=False, dim=3))
# Gravel drops flint, with 1 in 10 odds.
_add_block(Block(13, "gravel", drop=318, ratio=1 / 10))
# Leaves drop saplings, with 1 in 9 odds, and dims by 1.
_add_block(Block(18, "leaves", drop=6, ratio=1 / 9, dim=1))
# Torches are orientable.
_add_block(Block(50, "torch", orientation=(None, 5, 4, 3, 2, 1), dim=0))
# Furnaces are orientable.
_add_block(Block(61, "furnace", orientation=(0, 1, 2, 3, 4, 5)))
# Ladders are orientable.
_add_block(Block(65, "ladder", orientation=(None, None, 2, 3, 4, 5), dim=0))
# Redstone ore drops 5 redstone dusts.
_add_block(Block(73, "redstone-ore", drop=331, quantity=5))
_add_block(Block(74, "glowing-redstone-ore", drop=331, quantity=5))
# Redstone torches are orientable.
_add_block(Block(75, "redstone-torch-off", orientation=(None, 5, 4, 3, 2, 1), dim=0))
_add_block(Block(76, "redstone-torch", orientation=(None, 5, 4, 3, 2, 1), dim=0))
# Stone buttons are orientable.
_add_block(Block(77, "stone-button", orientation=(None, None, 1, 2, 3, 4), dim=0))
# Ice drops nothing, is replaced by springs, and dims by 3.
_add_block(Block(79, "ice", drop=0, replace=9, dim=3))
# Clay drops 4 clay balls.
_add_block(Block(82, "clay", drop=337, quantity=4))

for block in blocks.values():
    blocks[block.name] = block
    blocks[block.slot] = block

items = {}
"""
A dictionary of ``Item`` objects.

This dictionary can be indexed by slot number or block name.
"""

for i, name in enumerate(block_names):
    if not name or name in blocks:
        continue

    kwargs = {}
    if i in drops:
        kwargs["drop"] = drops[i]
    if i in unbreakables:
        kwargs["breakable"] = False
    if i in dims:
        kwargs["dim"] = dims[i]

    b = Block(i, name, **kwargs)
    _add_block(b)

for i, name in enumerate(item_names):
    kwargs = {}
    i += 0x100
    item = Item(i, name, **kwargs)
    items[i] = item
    items[name] = item

for i, name in enumerate(special_item_names):
    kwargs = {}
    i += 0x8D0
    item = Item(i, name, **kwargs)
    items[i] = item
    items[name] = item

_secondary_items = {
    items["coal"]: coal_names,
    items["dye"]: dye_names,
}

for base_item, names in _secondary_items.iteritems():
    for i, name in enumerate(names):
        kwargs = {}
        item = Item(base_item.slot, name, i, **kwargs)
        items[name] = item

_secondary_blocks = {
    blocks["leaves"]: leave_names,
    blocks["log"]: log_names,
    blocks["sapling"]: sapling_names,
    blocks["step"]: step_names,
    blocks["wool"]: wool_names,
}

for base_block, names in _secondary_blocks.iteritems():
    for i, name in enumerate(names):
        kwargs = {}
        kwargs["drop"] = base_block.drop
        kwargs["breakable"] = base_block.breakable
        kwargs["dim"] = base_block.dim

        block = Block(base_block.slot, name, i, **kwargs)
        _add_block(block)

glowing_blocks = {
    blocks["torch"].slot: 14,
    blocks["lightstone"].slot: 15,
    blocks["jack-o-lantern"].slot: 15,
    blocks["fire"].slot: 15,
    blocks["lava"].slot: 15,
    blocks["lava-spring"].slot: 15,
    blocks["locked-chest"].slot: 15,
    blocks["burning-furnace"].slot: 13,
    blocks["portal"].slot: 11,
    blocks["glowing-redstone-ore"].slot: 9,
    blocks["redstone-repeater-on"].slot: 9,
    blocks["redstone-torch"].slot: 7,
    blocks["brown-mushroom"].slot: 1,
}

armor_helmets = (86, 298, 302, 306, 310, 314)
"""
List of slots of helmets.

Note that slot 86 (pumpkin) is a helmet.
"""

armor_chestplates = (299, 303, 307, 311, 315)
"""
List of slots of chestplates.

Note that slot 303 (chainmail chestplate) is a chestplate, even though it is
not normally obtainable.
"""

armor_leggings = (300, 304, 308, 312, 316)
"""
List of slots of leggings.
"""

armor_boots = (301, 305, 309, 313, 317)
"""
List of slots of boots.
"""

def parse_block(block):
    """
    Get the key for a given block/item.
    """

    try:
        if block.startswith("0x") and (
            (int(block, 16) in blocks) or (int(block, 16) in items)):
            return (int(block, 16), 0)
        elif (int(block) in blocks) or (int(block) in items):
            return (int(block), 0)
        else:
            raise Exception("Couldn't find block id %s!" % block)
    except ValueError:
        if block in blocks:
            return blocks[block].key
        elif block in items:
            return items[block].key
        else:
            raise Exception("Couldn't parse block %s!" % block)
