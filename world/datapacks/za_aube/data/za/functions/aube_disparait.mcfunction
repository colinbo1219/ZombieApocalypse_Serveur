# fumée, puis disparition sans butin (hors de vue : aucun joueur à 24 blocs)
particle minecraft:large_smoke ~ ~1 ~ 0.3 0.6 0.3 0.01 12
data merge entity @s {DeathLootTable:"minecraft:empty"}
tp @s ~ -200 ~
kill @s
