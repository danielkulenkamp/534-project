set ns [new Simulator]
source tb_compat.tcl

set node01 [$ns node]
tb-fix-node node01 zotacB1
tb-set-node-os node01 UBUNTU-12-dkulenka-v

set node02 [$ns node]
tb-fix-node node02 zotacG1
tb-set-node-os node02 UBUNTU-12-dkulenka-v

set node03 [$ns node]
tb-fix-node node03 zotacF2
tb-set-node-os node03 UBUNTU-12-dkulenka-v

set node04 [$ns node]
tb-fix-node node04 zotacI4
tb-set-node-os node04 UBUNTU-12-dkulenka-v

set node05 [$ns node]
tb-fix-node node05 zotacJ6
tb-set-node-os node05 UBUNTU-12-dkulenka-v

set node06 [$ns node]
tb-fix-node node06 zotacH1
tb-set-node-os node06 UBUNTU-12-dkulenka-v

set node07 [$ns node]
tb-fix-node node07 zotacD6
tb-set-node-os node07 UBUNTU-12-dkulenka-v

set node08 [$ns node]
tb-fix-node node08 zotacF4
tb-set-node-os node08 UBUNTU-12-dkulenka-v

set node09 [$ns node]
tb-fix-node node09 zotacF6
tb-set-node-os node09 UBUNTU-12-dkulenka-v

set node10 [$ns node]
tb-fix-node node10 zotacC1
tb-set-node-os node10 UBUNTU-12-dkulenka-v

set node11 [$ns node]
tb-fix-node node11 zotacD1
tb-set-node-os node11 UBUNTU-12-dkulenka-v

set node12 [$ns node]
tb-fix-node node12 zotacE1
tb-set-node-os node12 UBUNTU-12-dkulenka-v

set node13 [$ns node]
tb-fix-node node13 zotacF1
tb-set-node-os node13 UBUNTU-12-dkulenka-v

set node14 [$ns node]
tb-fix-node node14 zotacF3
tb-set-node-os node14 UBUNTU-12-dkulenka-v

set node15 [$ns node]
tb-fix-node node15 zotacG3
tb-set-node-os node15 UBUNTU-12-dkulenka-v

set node16 [$ns node]
tb-fix-node node16 zotacG4
tb-set-node-os node16 UBUNTU-12-dkulenka-v

set node17 [$ns node]
tb-fix-node node17 zotacD3
tb-set-node-os node17 UBUNTU-12-dkulenka-v

set node18 [$ns node]
tb-fix-node node18 zotacI3
tb-set-node-os node18 UBUNTU-12-dkulenka-v

set node19 [$ns node]
tb-fix-node node19 zotacH2
tb-set-node-os node19 UBUNTU-12-dkulenka-v

set node20 [$ns node]
tb-fix-node node20 zotacH3
tb-set-node-os node20 UBUNTU-12-dkulenka-v

set node21 [$ns node]
tb-fix-node node21 zotacI1
tb-set-node-os node21 UBUNTU-12-dkulenka-v

set node22 [$ns node]
tb-fix-node node22 zotacI2
tb-set-node-os node22 UBUNTU-12-dkulenka-v

set node23 [$ns node]
tb-fix-node node23 zotacK2
tb-set-node-os node23 UBUNTU-12-dkulenka-v

set node24 [$ns node]
tb-fix-node node24 zotacH6
tb-set-node-os node24 UBUNTU-12-dkulenka-v

set node25 [$ns node]
tb-fix-node node25 zotacK3
tb-set-node-os node25 UBUNTU-12-dkulenka-v

set node26 [$ns node]
tb-fix-node node26 zotacC6
tb-set-node-os node26 UBUNTU-12-dkulenka-v

set node27 [$ns node]
tb-fix-node node27 zotacI6
tb-set-node-os node27 UBUNTU-12-dkulenka-v

set node28 [$ns node]
tb-fix-node node28 zotacJ3
tb-set-node-os node28 UBUNTU-12-dkulenka-v

set node29 [$ns node]
tb-fix-node node29 zotacK1
tb-set-node-os node29 UBUNTU-12-dkulenka-v

set node30 [$ns node]
tb-fix-node node30 zotacE4
tb-set-node-os node30 UBUNTU-12-dkulenka-v

set node31 [$ns node]
tb-fix-node node31 zotacM20
tb-set-node-os node31 UBUNTU-12-dkulenka-v

$ns run
