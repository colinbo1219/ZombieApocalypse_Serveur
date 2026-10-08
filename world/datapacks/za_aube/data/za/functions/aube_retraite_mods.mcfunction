# infectés de zombie_extreme : à ciel ouvert (sur le dessus du relief), à plus de 24 blocs de tout joueur -> rentrent au nid
execute as @e[type=#za:infectes_mods] at @s unless entity @a[distance=..24] positioned over motion_blocking_no_leaves if entity @s[distance=..2.5] at @s run function za:aube_disparait
