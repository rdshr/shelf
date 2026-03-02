# 4层置物架组合可视化总览

本目录由 `scripts/generate_shelf_combination_diagrams.py` 自动生成。
“组合原则通过”按 `R1-R7` 统一规则判定。

## 边界参数

- `N`(layers): 4
- `P`(payload per layer): 30.0
- `S`(space per layer): (80.0, 35.0, 30.0)
- `O`(opening): (65.0, 28.0)
- `A`(footprint): (90.0, 40.0)
- opening preference: direction=front, ratio=[0.6, 0.95]

## 统计

- 枚举组合总数: 192
- 组合原则通过数: 144

## 组合矩阵

| 组合ID | support_count | support_kind | orientation | connector | contour | opening_dir | 组合原则 | Mermaid | SVG | PNG |
|---|---:|---|---|---|---|---|---|---|---|---|
| COMBO-001 | 1 | rod | vertical | corner | aligned | front | `NO` | - | - | - |
| COMBO-002 | 1 | rod | vertical | corner | aligned | left | `NO` | - | - | - |
| COMBO-003 | 1 | rod | vertical | corner | staggered | front | `NO` | - | - | - |
| COMBO-004 | 1 | rod | vertical | corner | staggered | left | `NO` | - | - | - |
| COMBO-005 | 1 | rod | vertical | predefined_slot | aligned | front | `NO` | - | - | - |
| COMBO-006 | 1 | rod | vertical | predefined_slot | aligned | left | `NO` | - | - | - |
| COMBO-007 | 1 | rod | vertical | predefined_slot | staggered | front | `NO` | - | - | - |
| COMBO-008 | 1 | rod | vertical | predefined_slot | staggered | left | `NO` | - | - | - |
| COMBO-009 | 1 | rod | vertical | custom | aligned | front | `NO` | - | - | - |
| COMBO-010 | 1 | rod | vertical | custom | aligned | left | `NO` | - | - | - |
| COMBO-011 | 1 | rod | vertical | custom | staggered | front | `NO` | - | - | - |
| COMBO-012 | 1 | rod | vertical | custom | staggered | left | `NO` | - | - | - |
| COMBO-013 | 1 | rod | angled | corner | aligned | front | `NO` | - | - | - |
| COMBO-014 | 1 | rod | angled | corner | aligned | left | `NO` | - | - | - |
| COMBO-015 | 1 | rod | angled | corner | staggered | front | `NO` | - | - | - |
| COMBO-016 | 1 | rod | angled | corner | staggered | left | `NO` | - | - | - |
| COMBO-017 | 1 | rod | angled | predefined_slot | aligned | front | `NO` | - | - | - |
| COMBO-018 | 1 | rod | angled | predefined_slot | aligned | left | `NO` | - | - | - |
| COMBO-019 | 1 | rod | angled | predefined_slot | staggered | front | `NO` | - | - | - |
| COMBO-020 | 1 | rod | angled | predefined_slot | staggered | left | `NO` | - | - | - |
| COMBO-021 | 1 | rod | angled | custom | aligned | front | `NO` | - | - | - |
| COMBO-022 | 1 | rod | angled | custom | aligned | left | `NO` | - | - | - |
| COMBO-023 | 1 | rod | angled | custom | staggered | front | `NO` | - | - | - |
| COMBO-024 | 1 | rod | angled | custom | staggered | left | `NO` | - | - | - |
| COMBO-025 | 1 | panel | vertical | corner | aligned | front | `NO` | - | - | - |
| COMBO-026 | 1 | panel | vertical | corner | aligned | left | `NO` | - | - | - |
| COMBO-027 | 1 | panel | vertical | corner | staggered | front | `NO` | - | - | - |
| COMBO-028 | 1 | panel | vertical | corner | staggered | left | `NO` | - | - | - |
| COMBO-029 | 1 | panel | vertical | predefined_slot | aligned | front | `NO` | - | - | - |
| COMBO-030 | 1 | panel | vertical | predefined_slot | aligned | left | `NO` | - | - | - |
| COMBO-031 | 1 | panel | vertical | predefined_slot | staggered | front | `NO` | - | - | - |
| COMBO-032 | 1 | panel | vertical | predefined_slot | staggered | left | `NO` | - | - | - |
| COMBO-033 | 1 | panel | vertical | custom | aligned | front | `NO` | - | - | - |
| COMBO-034 | 1 | panel | vertical | custom | aligned | left | `NO` | - | - | - |
| COMBO-035 | 1 | panel | vertical | custom | staggered | front | `NO` | - | - | - |
| COMBO-036 | 1 | panel | vertical | custom | staggered | left | `NO` | - | - | - |
| COMBO-037 | 1 | panel | angled | corner | aligned | front | `NO` | - | - | - |
| COMBO-038 | 1 | panel | angled | corner | aligned | left | `NO` | - | - | - |
| COMBO-039 | 1 | panel | angled | corner | staggered | front | `NO` | - | - | - |
| COMBO-040 | 1 | panel | angled | corner | staggered | left | `NO` | - | - | - |
| COMBO-041 | 1 | panel | angled | predefined_slot | aligned | front | `NO` | - | - | - |
| COMBO-042 | 1 | panel | angled | predefined_slot | aligned | left | `NO` | - | - | - |
| COMBO-043 | 1 | panel | angled | predefined_slot | staggered | front | `NO` | - | - | - |
| COMBO-044 | 1 | panel | angled | predefined_slot | staggered | left | `NO` | - | - | - |
| COMBO-045 | 1 | panel | angled | custom | aligned | front | `NO` | - | - | - |
| COMBO-046 | 1 | panel | angled | custom | aligned | left | `NO` | - | - | - |
| COMBO-047 | 1 | panel | angled | custom | staggered | front | `NO` | - | - | - |
| COMBO-048 | 1 | panel | angled | custom | staggered | left | `NO` | - | - | - |
| COMBO-049 | 2 | rod | vertical | corner | aligned | front | `YES` | [COMBO-049.mmd](./COMBO-049.mmd) | [COMBO-049.svg](./COMBO-049.svg) | [COMBO-049.png](./COMBO-049.png) |
| COMBO-050 | 2 | rod | vertical | corner | aligned | left | `YES` | [COMBO-050.mmd](./COMBO-050.mmd) | [COMBO-050.svg](./COMBO-050.svg) | [COMBO-050.png](./COMBO-050.png) |
| COMBO-051 | 2 | rod | vertical | corner | staggered | front | `YES` | [COMBO-051.mmd](./COMBO-051.mmd) | [COMBO-051.svg](./COMBO-051.svg) | [COMBO-051.png](./COMBO-051.png) |
| COMBO-052 | 2 | rod | vertical | corner | staggered | left | `YES` | [COMBO-052.mmd](./COMBO-052.mmd) | [COMBO-052.svg](./COMBO-052.svg) | [COMBO-052.png](./COMBO-052.png) |
| COMBO-053 | 2 | rod | vertical | predefined_slot | aligned | front | `YES` | [COMBO-053.mmd](./COMBO-053.mmd) | [COMBO-053.svg](./COMBO-053.svg) | [COMBO-053.png](./COMBO-053.png) |
| COMBO-054 | 2 | rod | vertical | predefined_slot | aligned | left | `YES` | [COMBO-054.mmd](./COMBO-054.mmd) | [COMBO-054.svg](./COMBO-054.svg) | [COMBO-054.png](./COMBO-054.png) |
| COMBO-055 | 2 | rod | vertical | predefined_slot | staggered | front | `YES` | [COMBO-055.mmd](./COMBO-055.mmd) | [COMBO-055.svg](./COMBO-055.svg) | [COMBO-055.png](./COMBO-055.png) |
| COMBO-056 | 2 | rod | vertical | predefined_slot | staggered | left | `YES` | [COMBO-056.mmd](./COMBO-056.mmd) | [COMBO-056.svg](./COMBO-056.svg) | [COMBO-056.png](./COMBO-056.png) |
| COMBO-057 | 2 | rod | vertical | custom | aligned | front | `YES` | [COMBO-057.mmd](./COMBO-057.mmd) | [COMBO-057.svg](./COMBO-057.svg) | [COMBO-057.png](./COMBO-057.png) |
| COMBO-058 | 2 | rod | vertical | custom | aligned | left | `YES` | [COMBO-058.mmd](./COMBO-058.mmd) | [COMBO-058.svg](./COMBO-058.svg) | [COMBO-058.png](./COMBO-058.png) |
| COMBO-059 | 2 | rod | vertical | custom | staggered | front | `YES` | [COMBO-059.mmd](./COMBO-059.mmd) | [COMBO-059.svg](./COMBO-059.svg) | [COMBO-059.png](./COMBO-059.png) |
| COMBO-060 | 2 | rod | vertical | custom | staggered | left | `YES` | [COMBO-060.mmd](./COMBO-060.mmd) | [COMBO-060.svg](./COMBO-060.svg) | [COMBO-060.png](./COMBO-060.png) |
| COMBO-061 | 2 | rod | angled | corner | aligned | front | `YES` | [COMBO-061.mmd](./COMBO-061.mmd) | [COMBO-061.svg](./COMBO-061.svg) | [COMBO-061.png](./COMBO-061.png) |
| COMBO-062 | 2 | rod | angled | corner | aligned | left | `YES` | [COMBO-062.mmd](./COMBO-062.mmd) | [COMBO-062.svg](./COMBO-062.svg) | [COMBO-062.png](./COMBO-062.png) |
| COMBO-063 | 2 | rod | angled | corner | staggered | front | `YES` | [COMBO-063.mmd](./COMBO-063.mmd) | [COMBO-063.svg](./COMBO-063.svg) | [COMBO-063.png](./COMBO-063.png) |
| COMBO-064 | 2 | rod | angled | corner | staggered | left | `YES` | [COMBO-064.mmd](./COMBO-064.mmd) | [COMBO-064.svg](./COMBO-064.svg) | [COMBO-064.png](./COMBO-064.png) |
| COMBO-065 | 2 | rod | angled | predefined_slot | aligned | front | `YES` | [COMBO-065.mmd](./COMBO-065.mmd) | [COMBO-065.svg](./COMBO-065.svg) | [COMBO-065.png](./COMBO-065.png) |
| COMBO-066 | 2 | rod | angled | predefined_slot | aligned | left | `YES` | [COMBO-066.mmd](./COMBO-066.mmd) | [COMBO-066.svg](./COMBO-066.svg) | [COMBO-066.png](./COMBO-066.png) |
| COMBO-067 | 2 | rod | angled | predefined_slot | staggered | front | `YES` | [COMBO-067.mmd](./COMBO-067.mmd) | [COMBO-067.svg](./COMBO-067.svg) | [COMBO-067.png](./COMBO-067.png) |
| COMBO-068 | 2 | rod | angled | predefined_slot | staggered | left | `YES` | [COMBO-068.mmd](./COMBO-068.mmd) | [COMBO-068.svg](./COMBO-068.svg) | [COMBO-068.png](./COMBO-068.png) |
| COMBO-069 | 2 | rod | angled | custom | aligned | front | `YES` | [COMBO-069.mmd](./COMBO-069.mmd) | [COMBO-069.svg](./COMBO-069.svg) | [COMBO-069.png](./COMBO-069.png) |
| COMBO-070 | 2 | rod | angled | custom | aligned | left | `YES` | [COMBO-070.mmd](./COMBO-070.mmd) | [COMBO-070.svg](./COMBO-070.svg) | [COMBO-070.png](./COMBO-070.png) |
| COMBO-071 | 2 | rod | angled | custom | staggered | front | `YES` | [COMBO-071.mmd](./COMBO-071.mmd) | [COMBO-071.svg](./COMBO-071.svg) | [COMBO-071.png](./COMBO-071.png) |
| COMBO-072 | 2 | rod | angled | custom | staggered | left | `YES` | [COMBO-072.mmd](./COMBO-072.mmd) | [COMBO-072.svg](./COMBO-072.svg) | [COMBO-072.png](./COMBO-072.png) |
| COMBO-073 | 2 | panel | vertical | corner | aligned | front | `YES` | [COMBO-073.mmd](./COMBO-073.mmd) | [COMBO-073.svg](./COMBO-073.svg) | [COMBO-073.png](./COMBO-073.png) |
| COMBO-074 | 2 | panel | vertical | corner | aligned | left | `YES` | [COMBO-074.mmd](./COMBO-074.mmd) | [COMBO-074.svg](./COMBO-074.svg) | [COMBO-074.png](./COMBO-074.png) |
| COMBO-075 | 2 | panel | vertical | corner | staggered | front | `YES` | [COMBO-075.mmd](./COMBO-075.mmd) | [COMBO-075.svg](./COMBO-075.svg) | [COMBO-075.png](./COMBO-075.png) |
| COMBO-076 | 2 | panel | vertical | corner | staggered | left | `YES` | [COMBO-076.mmd](./COMBO-076.mmd) | [COMBO-076.svg](./COMBO-076.svg) | [COMBO-076.png](./COMBO-076.png) |
| COMBO-077 | 2 | panel | vertical | predefined_slot | aligned | front | `YES` | [COMBO-077.mmd](./COMBO-077.mmd) | [COMBO-077.svg](./COMBO-077.svg) | [COMBO-077.png](./COMBO-077.png) |
| COMBO-078 | 2 | panel | vertical | predefined_slot | aligned | left | `YES` | [COMBO-078.mmd](./COMBO-078.mmd) | [COMBO-078.svg](./COMBO-078.svg) | [COMBO-078.png](./COMBO-078.png) |
| COMBO-079 | 2 | panel | vertical | predefined_slot | staggered | front | `YES` | [COMBO-079.mmd](./COMBO-079.mmd) | [COMBO-079.svg](./COMBO-079.svg) | [COMBO-079.png](./COMBO-079.png) |
| COMBO-080 | 2 | panel | vertical | predefined_slot | staggered | left | `YES` | [COMBO-080.mmd](./COMBO-080.mmd) | [COMBO-080.svg](./COMBO-080.svg) | [COMBO-080.png](./COMBO-080.png) |
| COMBO-081 | 2 | panel | vertical | custom | aligned | front | `YES` | [COMBO-081.mmd](./COMBO-081.mmd) | [COMBO-081.svg](./COMBO-081.svg) | [COMBO-081.png](./COMBO-081.png) |
| COMBO-082 | 2 | panel | vertical | custom | aligned | left | `YES` | [COMBO-082.mmd](./COMBO-082.mmd) | [COMBO-082.svg](./COMBO-082.svg) | [COMBO-082.png](./COMBO-082.png) |
| COMBO-083 | 2 | panel | vertical | custom | staggered | front | `YES` | [COMBO-083.mmd](./COMBO-083.mmd) | [COMBO-083.svg](./COMBO-083.svg) | [COMBO-083.png](./COMBO-083.png) |
| COMBO-084 | 2 | panel | vertical | custom | staggered | left | `YES` | [COMBO-084.mmd](./COMBO-084.mmd) | [COMBO-084.svg](./COMBO-084.svg) | [COMBO-084.png](./COMBO-084.png) |
| COMBO-085 | 2 | panel | angled | corner | aligned | front | `YES` | [COMBO-085.mmd](./COMBO-085.mmd) | [COMBO-085.svg](./COMBO-085.svg) | [COMBO-085.png](./COMBO-085.png) |
| COMBO-086 | 2 | panel | angled | corner | aligned | left | `YES` | [COMBO-086.mmd](./COMBO-086.mmd) | [COMBO-086.svg](./COMBO-086.svg) | [COMBO-086.png](./COMBO-086.png) |
| COMBO-087 | 2 | panel | angled | corner | staggered | front | `YES` | [COMBO-087.mmd](./COMBO-087.mmd) | [COMBO-087.svg](./COMBO-087.svg) | [COMBO-087.png](./COMBO-087.png) |
| COMBO-088 | 2 | panel | angled | corner | staggered | left | `YES` | [COMBO-088.mmd](./COMBO-088.mmd) | [COMBO-088.svg](./COMBO-088.svg) | [COMBO-088.png](./COMBO-088.png) |
| COMBO-089 | 2 | panel | angled | predefined_slot | aligned | front | `YES` | [COMBO-089.mmd](./COMBO-089.mmd) | [COMBO-089.svg](./COMBO-089.svg) | [COMBO-089.png](./COMBO-089.png) |
| COMBO-090 | 2 | panel | angled | predefined_slot | aligned | left | `YES` | [COMBO-090.mmd](./COMBO-090.mmd) | [COMBO-090.svg](./COMBO-090.svg) | [COMBO-090.png](./COMBO-090.png) |
| COMBO-091 | 2 | panel | angled | predefined_slot | staggered | front | `YES` | [COMBO-091.mmd](./COMBO-091.mmd) | [COMBO-091.svg](./COMBO-091.svg) | [COMBO-091.png](./COMBO-091.png) |
| COMBO-092 | 2 | panel | angled | predefined_slot | staggered | left | `YES` | [COMBO-092.mmd](./COMBO-092.mmd) | [COMBO-092.svg](./COMBO-092.svg) | [COMBO-092.png](./COMBO-092.png) |
| COMBO-093 | 2 | panel | angled | custom | aligned | front | `YES` | [COMBO-093.mmd](./COMBO-093.mmd) | [COMBO-093.svg](./COMBO-093.svg) | [COMBO-093.png](./COMBO-093.png) |
| COMBO-094 | 2 | panel | angled | custom | aligned | left | `YES` | [COMBO-094.mmd](./COMBO-094.mmd) | [COMBO-094.svg](./COMBO-094.svg) | [COMBO-094.png](./COMBO-094.png) |
| COMBO-095 | 2 | panel | angled | custom | staggered | front | `YES` | [COMBO-095.mmd](./COMBO-095.mmd) | [COMBO-095.svg](./COMBO-095.svg) | [COMBO-095.png](./COMBO-095.png) |
| COMBO-096 | 2 | panel | angled | custom | staggered | left | `YES` | [COMBO-096.mmd](./COMBO-096.mmd) | [COMBO-096.svg](./COMBO-096.svg) | [COMBO-096.png](./COMBO-096.png) |
| COMBO-097 | 3 | rod | vertical | corner | aligned | front | `YES` | [COMBO-097.mmd](./COMBO-097.mmd) | [COMBO-097.svg](./COMBO-097.svg) | [COMBO-097.png](./COMBO-097.png) |
| COMBO-098 | 3 | rod | vertical | corner | aligned | left | `YES` | [COMBO-098.mmd](./COMBO-098.mmd) | [COMBO-098.svg](./COMBO-098.svg) | [COMBO-098.png](./COMBO-098.png) |
| COMBO-099 | 3 | rod | vertical | corner | staggered | front | `YES` | [COMBO-099.mmd](./COMBO-099.mmd) | [COMBO-099.svg](./COMBO-099.svg) | [COMBO-099.png](./COMBO-099.png) |
| COMBO-100 | 3 | rod | vertical | corner | staggered | left | `YES` | [COMBO-100.mmd](./COMBO-100.mmd) | [COMBO-100.svg](./COMBO-100.svg) | [COMBO-100.png](./COMBO-100.png) |
| COMBO-101 | 3 | rod | vertical | predefined_slot | aligned | front | `YES` | [COMBO-101.mmd](./COMBO-101.mmd) | [COMBO-101.svg](./COMBO-101.svg) | [COMBO-101.png](./COMBO-101.png) |
| COMBO-102 | 3 | rod | vertical | predefined_slot | aligned | left | `YES` | [COMBO-102.mmd](./COMBO-102.mmd) | [COMBO-102.svg](./COMBO-102.svg) | [COMBO-102.png](./COMBO-102.png) |
| COMBO-103 | 3 | rod | vertical | predefined_slot | staggered | front | `YES` | [COMBO-103.mmd](./COMBO-103.mmd) | [COMBO-103.svg](./COMBO-103.svg) | [COMBO-103.png](./COMBO-103.png) |
| COMBO-104 | 3 | rod | vertical | predefined_slot | staggered | left | `YES` | [COMBO-104.mmd](./COMBO-104.mmd) | [COMBO-104.svg](./COMBO-104.svg) | [COMBO-104.png](./COMBO-104.png) |
| COMBO-105 | 3 | rod | vertical | custom | aligned | front | `YES` | [COMBO-105.mmd](./COMBO-105.mmd) | [COMBO-105.svg](./COMBO-105.svg) | [COMBO-105.png](./COMBO-105.png) |
| COMBO-106 | 3 | rod | vertical | custom | aligned | left | `YES` | [COMBO-106.mmd](./COMBO-106.mmd) | [COMBO-106.svg](./COMBO-106.svg) | [COMBO-106.png](./COMBO-106.png) |
| COMBO-107 | 3 | rod | vertical | custom | staggered | front | `YES` | [COMBO-107.mmd](./COMBO-107.mmd) | [COMBO-107.svg](./COMBO-107.svg) | [COMBO-107.png](./COMBO-107.png) |
| COMBO-108 | 3 | rod | vertical | custom | staggered | left | `YES` | [COMBO-108.mmd](./COMBO-108.mmd) | [COMBO-108.svg](./COMBO-108.svg) | [COMBO-108.png](./COMBO-108.png) |
| COMBO-109 | 3 | rod | angled | corner | aligned | front | `YES` | [COMBO-109.mmd](./COMBO-109.mmd) | [COMBO-109.svg](./COMBO-109.svg) | [COMBO-109.png](./COMBO-109.png) |
| COMBO-110 | 3 | rod | angled | corner | aligned | left | `YES` | [COMBO-110.mmd](./COMBO-110.mmd) | [COMBO-110.svg](./COMBO-110.svg) | [COMBO-110.png](./COMBO-110.png) |
| COMBO-111 | 3 | rod | angled | corner | staggered | front | `YES` | [COMBO-111.mmd](./COMBO-111.mmd) | [COMBO-111.svg](./COMBO-111.svg) | [COMBO-111.png](./COMBO-111.png) |
| COMBO-112 | 3 | rod | angled | corner | staggered | left | `YES` | [COMBO-112.mmd](./COMBO-112.mmd) | [COMBO-112.svg](./COMBO-112.svg) | [COMBO-112.png](./COMBO-112.png) |
| COMBO-113 | 3 | rod | angled | predefined_slot | aligned | front | `YES` | [COMBO-113.mmd](./COMBO-113.mmd) | [COMBO-113.svg](./COMBO-113.svg) | [COMBO-113.png](./COMBO-113.png) |
| COMBO-114 | 3 | rod | angled | predefined_slot | aligned | left | `YES` | [COMBO-114.mmd](./COMBO-114.mmd) | [COMBO-114.svg](./COMBO-114.svg) | [COMBO-114.png](./COMBO-114.png) |
| COMBO-115 | 3 | rod | angled | predefined_slot | staggered | front | `YES` | [COMBO-115.mmd](./COMBO-115.mmd) | [COMBO-115.svg](./COMBO-115.svg) | [COMBO-115.png](./COMBO-115.png) |
| COMBO-116 | 3 | rod | angled | predefined_slot | staggered | left | `YES` | [COMBO-116.mmd](./COMBO-116.mmd) | [COMBO-116.svg](./COMBO-116.svg) | [COMBO-116.png](./COMBO-116.png) |
| COMBO-117 | 3 | rod | angled | custom | aligned | front | `YES` | [COMBO-117.mmd](./COMBO-117.mmd) | [COMBO-117.svg](./COMBO-117.svg) | [COMBO-117.png](./COMBO-117.png) |
| COMBO-118 | 3 | rod | angled | custom | aligned | left | `YES` | [COMBO-118.mmd](./COMBO-118.mmd) | [COMBO-118.svg](./COMBO-118.svg) | [COMBO-118.png](./COMBO-118.png) |
| COMBO-119 | 3 | rod | angled | custom | staggered | front | `YES` | [COMBO-119.mmd](./COMBO-119.mmd) | [COMBO-119.svg](./COMBO-119.svg) | [COMBO-119.png](./COMBO-119.png) |
| COMBO-120 | 3 | rod | angled | custom | staggered | left | `YES` | [COMBO-120.mmd](./COMBO-120.mmd) | [COMBO-120.svg](./COMBO-120.svg) | [COMBO-120.png](./COMBO-120.png) |
| COMBO-121 | 3 | panel | vertical | corner | aligned | front | `YES` | [COMBO-121.mmd](./COMBO-121.mmd) | [COMBO-121.svg](./COMBO-121.svg) | [COMBO-121.png](./COMBO-121.png) |
| COMBO-122 | 3 | panel | vertical | corner | aligned | left | `YES` | [COMBO-122.mmd](./COMBO-122.mmd) | [COMBO-122.svg](./COMBO-122.svg) | [COMBO-122.png](./COMBO-122.png) |
| COMBO-123 | 3 | panel | vertical | corner | staggered | front | `YES` | [COMBO-123.mmd](./COMBO-123.mmd) | [COMBO-123.svg](./COMBO-123.svg) | [COMBO-123.png](./COMBO-123.png) |
| COMBO-124 | 3 | panel | vertical | corner | staggered | left | `YES` | [COMBO-124.mmd](./COMBO-124.mmd) | [COMBO-124.svg](./COMBO-124.svg) | [COMBO-124.png](./COMBO-124.png) |
| COMBO-125 | 3 | panel | vertical | predefined_slot | aligned | front | `YES` | [COMBO-125.mmd](./COMBO-125.mmd) | [COMBO-125.svg](./COMBO-125.svg) | [COMBO-125.png](./COMBO-125.png) |
| COMBO-126 | 3 | panel | vertical | predefined_slot | aligned | left | `YES` | [COMBO-126.mmd](./COMBO-126.mmd) | [COMBO-126.svg](./COMBO-126.svg) | [COMBO-126.png](./COMBO-126.png) |
| COMBO-127 | 3 | panel | vertical | predefined_slot | staggered | front | `YES` | [COMBO-127.mmd](./COMBO-127.mmd) | [COMBO-127.svg](./COMBO-127.svg) | [COMBO-127.png](./COMBO-127.png) |
| COMBO-128 | 3 | panel | vertical | predefined_slot | staggered | left | `YES` | [COMBO-128.mmd](./COMBO-128.mmd) | [COMBO-128.svg](./COMBO-128.svg) | [COMBO-128.png](./COMBO-128.png) |
| COMBO-129 | 3 | panel | vertical | custom | aligned | front | `YES` | [COMBO-129.mmd](./COMBO-129.mmd) | [COMBO-129.svg](./COMBO-129.svg) | [COMBO-129.png](./COMBO-129.png) |
| COMBO-130 | 3 | panel | vertical | custom | aligned | left | `YES` | [COMBO-130.mmd](./COMBO-130.mmd) | [COMBO-130.svg](./COMBO-130.svg) | [COMBO-130.png](./COMBO-130.png) |
| COMBO-131 | 3 | panel | vertical | custom | staggered | front | `YES` | [COMBO-131.mmd](./COMBO-131.mmd) | [COMBO-131.svg](./COMBO-131.svg) | [COMBO-131.png](./COMBO-131.png) |
| COMBO-132 | 3 | panel | vertical | custom | staggered | left | `YES` | [COMBO-132.mmd](./COMBO-132.mmd) | [COMBO-132.svg](./COMBO-132.svg) | [COMBO-132.png](./COMBO-132.png) |
| COMBO-133 | 3 | panel | angled | corner | aligned | front | `YES` | [COMBO-133.mmd](./COMBO-133.mmd) | [COMBO-133.svg](./COMBO-133.svg) | [COMBO-133.png](./COMBO-133.png) |
| COMBO-134 | 3 | panel | angled | corner | aligned | left | `YES` | [COMBO-134.mmd](./COMBO-134.mmd) | [COMBO-134.svg](./COMBO-134.svg) | [COMBO-134.png](./COMBO-134.png) |
| COMBO-135 | 3 | panel | angled | corner | staggered | front | `YES` | [COMBO-135.mmd](./COMBO-135.mmd) | [COMBO-135.svg](./COMBO-135.svg) | [COMBO-135.png](./COMBO-135.png) |
| COMBO-136 | 3 | panel | angled | corner | staggered | left | `YES` | [COMBO-136.mmd](./COMBO-136.mmd) | [COMBO-136.svg](./COMBO-136.svg) | [COMBO-136.png](./COMBO-136.png) |
| COMBO-137 | 3 | panel | angled | predefined_slot | aligned | front | `YES` | [COMBO-137.mmd](./COMBO-137.mmd) | [COMBO-137.svg](./COMBO-137.svg) | [COMBO-137.png](./COMBO-137.png) |
| COMBO-138 | 3 | panel | angled | predefined_slot | aligned | left | `YES` | [COMBO-138.mmd](./COMBO-138.mmd) | [COMBO-138.svg](./COMBO-138.svg) | [COMBO-138.png](./COMBO-138.png) |
| COMBO-139 | 3 | panel | angled | predefined_slot | staggered | front | `YES` | [COMBO-139.mmd](./COMBO-139.mmd) | [COMBO-139.svg](./COMBO-139.svg) | [COMBO-139.png](./COMBO-139.png) |
| COMBO-140 | 3 | panel | angled | predefined_slot | staggered | left | `YES` | [COMBO-140.mmd](./COMBO-140.mmd) | [COMBO-140.svg](./COMBO-140.svg) | [COMBO-140.png](./COMBO-140.png) |
| COMBO-141 | 3 | panel | angled | custom | aligned | front | `YES` | [COMBO-141.mmd](./COMBO-141.mmd) | [COMBO-141.svg](./COMBO-141.svg) | [COMBO-141.png](./COMBO-141.png) |
| COMBO-142 | 3 | panel | angled | custom | aligned | left | `YES` | [COMBO-142.mmd](./COMBO-142.mmd) | [COMBO-142.svg](./COMBO-142.svg) | [COMBO-142.png](./COMBO-142.png) |
| COMBO-143 | 3 | panel | angled | custom | staggered | front | `YES` | [COMBO-143.mmd](./COMBO-143.mmd) | [COMBO-143.svg](./COMBO-143.svg) | [COMBO-143.png](./COMBO-143.png) |
| COMBO-144 | 3 | panel | angled | custom | staggered | left | `YES` | [COMBO-144.mmd](./COMBO-144.mmd) | [COMBO-144.svg](./COMBO-144.svg) | [COMBO-144.png](./COMBO-144.png) |
| COMBO-145 | 4 | rod | vertical | corner | aligned | front | `YES` | [COMBO-145.mmd](./COMBO-145.mmd) | [COMBO-145.svg](./COMBO-145.svg) | [COMBO-145.png](./COMBO-145.png) |
| COMBO-146 | 4 | rod | vertical | corner | aligned | left | `YES` | [COMBO-146.mmd](./COMBO-146.mmd) | [COMBO-146.svg](./COMBO-146.svg) | [COMBO-146.png](./COMBO-146.png) |
| COMBO-147 | 4 | rod | vertical | corner | staggered | front | `YES` | [COMBO-147.mmd](./COMBO-147.mmd) | [COMBO-147.svg](./COMBO-147.svg) | [COMBO-147.png](./COMBO-147.png) |
| COMBO-148 | 4 | rod | vertical | corner | staggered | left | `YES` | [COMBO-148.mmd](./COMBO-148.mmd) | [COMBO-148.svg](./COMBO-148.svg) | [COMBO-148.png](./COMBO-148.png) |
| COMBO-149 | 4 | rod | vertical | predefined_slot | aligned | front | `YES` | [COMBO-149.mmd](./COMBO-149.mmd) | [COMBO-149.svg](./COMBO-149.svg) | [COMBO-149.png](./COMBO-149.png) |
| COMBO-150 | 4 | rod | vertical | predefined_slot | aligned | left | `YES` | [COMBO-150.mmd](./COMBO-150.mmd) | [COMBO-150.svg](./COMBO-150.svg) | [COMBO-150.png](./COMBO-150.png) |
| COMBO-151 | 4 | rod | vertical | predefined_slot | staggered | front | `YES` | [COMBO-151.mmd](./COMBO-151.mmd) | [COMBO-151.svg](./COMBO-151.svg) | [COMBO-151.png](./COMBO-151.png) |
| COMBO-152 | 4 | rod | vertical | predefined_slot | staggered | left | `YES` | [COMBO-152.mmd](./COMBO-152.mmd) | [COMBO-152.svg](./COMBO-152.svg) | [COMBO-152.png](./COMBO-152.png) |
| COMBO-153 | 4 | rod | vertical | custom | aligned | front | `YES` | [COMBO-153.mmd](./COMBO-153.mmd) | [COMBO-153.svg](./COMBO-153.svg) | [COMBO-153.png](./COMBO-153.png) |
| COMBO-154 | 4 | rod | vertical | custom | aligned | left | `YES` | [COMBO-154.mmd](./COMBO-154.mmd) | [COMBO-154.svg](./COMBO-154.svg) | [COMBO-154.png](./COMBO-154.png) |
| COMBO-155 | 4 | rod | vertical | custom | staggered | front | `YES` | [COMBO-155.mmd](./COMBO-155.mmd) | [COMBO-155.svg](./COMBO-155.svg) | [COMBO-155.png](./COMBO-155.png) |
| COMBO-156 | 4 | rod | vertical | custom | staggered | left | `YES` | [COMBO-156.mmd](./COMBO-156.mmd) | [COMBO-156.svg](./COMBO-156.svg) | [COMBO-156.png](./COMBO-156.png) |
| COMBO-157 | 4 | rod | angled | corner | aligned | front | `YES` | [COMBO-157.mmd](./COMBO-157.mmd) | [COMBO-157.svg](./COMBO-157.svg) | [COMBO-157.png](./COMBO-157.png) |
| COMBO-158 | 4 | rod | angled | corner | aligned | left | `YES` | [COMBO-158.mmd](./COMBO-158.mmd) | [COMBO-158.svg](./COMBO-158.svg) | [COMBO-158.png](./COMBO-158.png) |
| COMBO-159 | 4 | rod | angled | corner | staggered | front | `YES` | [COMBO-159.mmd](./COMBO-159.mmd) | [COMBO-159.svg](./COMBO-159.svg) | [COMBO-159.png](./COMBO-159.png) |
| COMBO-160 | 4 | rod | angled | corner | staggered | left | `YES` | [COMBO-160.mmd](./COMBO-160.mmd) | [COMBO-160.svg](./COMBO-160.svg) | [COMBO-160.png](./COMBO-160.png) |
| COMBO-161 | 4 | rod | angled | predefined_slot | aligned | front | `YES` | [COMBO-161.mmd](./COMBO-161.mmd) | [COMBO-161.svg](./COMBO-161.svg) | [COMBO-161.png](./COMBO-161.png) |
| COMBO-162 | 4 | rod | angled | predefined_slot | aligned | left | `YES` | [COMBO-162.mmd](./COMBO-162.mmd) | [COMBO-162.svg](./COMBO-162.svg) | [COMBO-162.png](./COMBO-162.png) |
| COMBO-163 | 4 | rod | angled | predefined_slot | staggered | front | `YES` | [COMBO-163.mmd](./COMBO-163.mmd) | [COMBO-163.svg](./COMBO-163.svg) | [COMBO-163.png](./COMBO-163.png) |
| COMBO-164 | 4 | rod | angled | predefined_slot | staggered | left | `YES` | [COMBO-164.mmd](./COMBO-164.mmd) | [COMBO-164.svg](./COMBO-164.svg) | [COMBO-164.png](./COMBO-164.png) |
| COMBO-165 | 4 | rod | angled | custom | aligned | front | `YES` | [COMBO-165.mmd](./COMBO-165.mmd) | [COMBO-165.svg](./COMBO-165.svg) | [COMBO-165.png](./COMBO-165.png) |
| COMBO-166 | 4 | rod | angled | custom | aligned | left | `YES` | [COMBO-166.mmd](./COMBO-166.mmd) | [COMBO-166.svg](./COMBO-166.svg) | [COMBO-166.png](./COMBO-166.png) |
| COMBO-167 | 4 | rod | angled | custom | staggered | front | `YES` | [COMBO-167.mmd](./COMBO-167.mmd) | [COMBO-167.svg](./COMBO-167.svg) | [COMBO-167.png](./COMBO-167.png) |
| COMBO-168 | 4 | rod | angled | custom | staggered | left | `YES` | [COMBO-168.mmd](./COMBO-168.mmd) | [COMBO-168.svg](./COMBO-168.svg) | [COMBO-168.png](./COMBO-168.png) |
| COMBO-169 | 4 | panel | vertical | corner | aligned | front | `YES` | [COMBO-169.mmd](./COMBO-169.mmd) | [COMBO-169.svg](./COMBO-169.svg) | [COMBO-169.png](./COMBO-169.png) |
| COMBO-170 | 4 | panel | vertical | corner | aligned | left | `YES` | [COMBO-170.mmd](./COMBO-170.mmd) | [COMBO-170.svg](./COMBO-170.svg) | [COMBO-170.png](./COMBO-170.png) |
| COMBO-171 | 4 | panel | vertical | corner | staggered | front | `YES` | [COMBO-171.mmd](./COMBO-171.mmd) | [COMBO-171.svg](./COMBO-171.svg) | [COMBO-171.png](./COMBO-171.png) |
| COMBO-172 | 4 | panel | vertical | corner | staggered | left | `YES` | [COMBO-172.mmd](./COMBO-172.mmd) | [COMBO-172.svg](./COMBO-172.svg) | [COMBO-172.png](./COMBO-172.png) |
| COMBO-173 | 4 | panel | vertical | predefined_slot | aligned | front | `YES` | [COMBO-173.mmd](./COMBO-173.mmd) | [COMBO-173.svg](./COMBO-173.svg) | [COMBO-173.png](./COMBO-173.png) |
| COMBO-174 | 4 | panel | vertical | predefined_slot | aligned | left | `YES` | [COMBO-174.mmd](./COMBO-174.mmd) | [COMBO-174.svg](./COMBO-174.svg) | [COMBO-174.png](./COMBO-174.png) |
| COMBO-175 | 4 | panel | vertical | predefined_slot | staggered | front | `YES` | [COMBO-175.mmd](./COMBO-175.mmd) | [COMBO-175.svg](./COMBO-175.svg) | [COMBO-175.png](./COMBO-175.png) |
| COMBO-176 | 4 | panel | vertical | predefined_slot | staggered | left | `YES` | [COMBO-176.mmd](./COMBO-176.mmd) | [COMBO-176.svg](./COMBO-176.svg) | [COMBO-176.png](./COMBO-176.png) |
| COMBO-177 | 4 | panel | vertical | custom | aligned | front | `YES` | [COMBO-177.mmd](./COMBO-177.mmd) | [COMBO-177.svg](./COMBO-177.svg) | [COMBO-177.png](./COMBO-177.png) |
| COMBO-178 | 4 | panel | vertical | custom | aligned | left | `YES` | [COMBO-178.mmd](./COMBO-178.mmd) | [COMBO-178.svg](./COMBO-178.svg) | [COMBO-178.png](./COMBO-178.png) |
| COMBO-179 | 4 | panel | vertical | custom | staggered | front | `YES` | [COMBO-179.mmd](./COMBO-179.mmd) | [COMBO-179.svg](./COMBO-179.svg) | [COMBO-179.png](./COMBO-179.png) |
| COMBO-180 | 4 | panel | vertical | custom | staggered | left | `YES` | [COMBO-180.mmd](./COMBO-180.mmd) | [COMBO-180.svg](./COMBO-180.svg) | [COMBO-180.png](./COMBO-180.png) |
| COMBO-181 | 4 | panel | angled | corner | aligned | front | `YES` | [COMBO-181.mmd](./COMBO-181.mmd) | [COMBO-181.svg](./COMBO-181.svg) | [COMBO-181.png](./COMBO-181.png) |
| COMBO-182 | 4 | panel | angled | corner | aligned | left | `YES` | [COMBO-182.mmd](./COMBO-182.mmd) | [COMBO-182.svg](./COMBO-182.svg) | [COMBO-182.png](./COMBO-182.png) |
| COMBO-183 | 4 | panel | angled | corner | staggered | front | `YES` | [COMBO-183.mmd](./COMBO-183.mmd) | [COMBO-183.svg](./COMBO-183.svg) | [COMBO-183.png](./COMBO-183.png) |
| COMBO-184 | 4 | panel | angled | corner | staggered | left | `YES` | [COMBO-184.mmd](./COMBO-184.mmd) | [COMBO-184.svg](./COMBO-184.svg) | [COMBO-184.png](./COMBO-184.png) |
| COMBO-185 | 4 | panel | angled | predefined_slot | aligned | front | `YES` | [COMBO-185.mmd](./COMBO-185.mmd) | [COMBO-185.svg](./COMBO-185.svg) | [COMBO-185.png](./COMBO-185.png) |
| COMBO-186 | 4 | panel | angled | predefined_slot | aligned | left | `YES` | [COMBO-186.mmd](./COMBO-186.mmd) | [COMBO-186.svg](./COMBO-186.svg) | [COMBO-186.png](./COMBO-186.png) |
| COMBO-187 | 4 | panel | angled | predefined_slot | staggered | front | `YES` | [COMBO-187.mmd](./COMBO-187.mmd) | [COMBO-187.svg](./COMBO-187.svg) | [COMBO-187.png](./COMBO-187.png) |
| COMBO-188 | 4 | panel | angled | predefined_slot | staggered | left | `YES` | [COMBO-188.mmd](./COMBO-188.mmd) | [COMBO-188.svg](./COMBO-188.svg) | [COMBO-188.png](./COMBO-188.png) |
| COMBO-189 | 4 | panel | angled | custom | aligned | front | `YES` | [COMBO-189.mmd](./COMBO-189.mmd) | [COMBO-189.svg](./COMBO-189.svg) | [COMBO-189.png](./COMBO-189.png) |
| COMBO-190 | 4 | panel | angled | custom | aligned | left | `YES` | [COMBO-190.mmd](./COMBO-190.mmd) | [COMBO-190.svg](./COMBO-190.svg) | [COMBO-190.png](./COMBO-190.png) |
| COMBO-191 | 4 | panel | angled | custom | staggered | front | `YES` | [COMBO-191.mmd](./COMBO-191.mmd) | [COMBO-191.svg](./COMBO-191.svg) | [COMBO-191.png](./COMBO-191.png) |
| COMBO-192 | 4 | panel | angled | custom | staggered | left | `YES` | [COMBO-192.mmd](./COMBO-192.mmd) | [COMBO-192.svg](./COMBO-192.svg) | [COMBO-192.png](./COMBO-192.png) |

## 使用命令

```bash
uv run python scripts/generate_shelf_combination_diagrams.py
```

可通过命令行参数修改边界和组合枚举范围。
