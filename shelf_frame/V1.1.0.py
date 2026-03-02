# -*- coding: utf-8 -*-
"""
将“置物架/立体堆叠装置”描述严格一一对应为代码（单文件）

### 目标：
定义一种可拆卸组装的开放式的立体堆叠装置，用于增加单位占地面积的存取物品的效率

### 边界：
装置具有一定承载重量限制
装置每层具有一定高度限制
装置层数需要有范围限制
装置本身需要占地面积限制
装置由一定数量独立的零件构成
装置对外通道开口面积有范围限制

### 最小完备基：
支撑系统：支撑柱
承载系统：平面板
链接系统：榫卯、螺钉

### 组合规则：
原则：
支撑系统和承载系统归类为功能
链接系统归类为接口
功能与功能之间需要通过接口进行连接
接口需要连接两个及两个以上的功能
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Sequence
from abc import ABC, abstractmethod


# =========================
# 基础类型与范围约束
# =========================

Number = float


@dataclass(frozen=True)
class Range:
    """数值范围（含边界）"""
    min_value: Number
    max_value: Number

    def contains(self, x: Number) -> bool:
        return self.min_value <= x <= self.max_value

    def validate(self, x: Number, name: str) -> None:
        if not self.contains(x):
            raise ValueError(f"{name}={x} 不在范围 [{self.min_value}, {self.max_value}] 内")


# =========================
# 组合规则：功能/接口
# =========================

class Part(ABC):
    """装置由一定数量独立的零件构成（零件抽象）"""

    @property
    @abstractmethod
    def part_name(self) -> str:
        raise NotImplementedError


class FunctionalPart(Part, ABC):
    """
    支撑系统和承载系统归类为功能
    """
    pass


class InterfacePart(Part, ABC):
    """
    链接系统归类为接口
    接口需要连接两个及两个以上的功能
    """

    @property
    @abstractmethod
    def linked_functional_parts(self) -> Tuple[FunctionalPart, ...]:
        raise NotImplementedError

    def validate_links(self) -> None:
        fps = self.linked_functional_parts
        if len(fps) < 2:
            raise ValueError("接口需要连接两个及两个以上的功能（linked_functional_parts 数量不足）")


# =========================
# 最小完备基：支撑柱 / 平面板 / 榫卯 / 螺钉
# =========================

@dataclass(frozen=True)
class SupportColumn(FunctionalPart):
    """
    支撑系统：支撑柱
    - 多层结构中用于层与层之间隔离（撑高）
    """
    height: Number  # 单根支撑柱高度（用于“层高*层数”的构成）
    max_axial_load: Number  # 轴向承载能力（可用于整体承载核算）

    @property
    def part_name(self) -> str:
        return "支撑柱"


@dataclass(frozen=True)
class PlaneBoard(FunctionalPart):
    """
    承载系统：平面板
    - 用于承载物品
    """
    length: Number
    width: Number
    thickness: Number
    max_surface_load: Number  # 板面承载能力（可用于整体承载核算）

    @property
    def area(self) -> Number:
        return self.length * self.width

    @property
    def part_name(self) -> str:
        return "平面板"


@dataclass(frozen=True)
class TenonMortise(InterfacePart):
    """
    链接系统：榫卯
    - 用于将平面板与支撑柱连接（接口转换、对齐、固定）
    """
    _linked: Tuple[FunctionalPart, ...]

    @property
    def linked_functional_parts(self) -> Tuple[FunctionalPart, ...]:
        return self._linked

    @property
    def part_name(self) -> str:
        return "榫卯"


@dataclass(frozen=True)
class Screw(InterfacePart):
    """
    链接系统：螺钉
    - 用于将平面板与支撑柱连接（接口转换、对齐、固定）
    """
    _linked: Tuple[FunctionalPart, ...]
    diameter: Number
    length: Number

    @property
    def linked_functional_parts(self) -> Tuple[FunctionalPart, ...]:
        return self._linked

    @property
    def part_name(self) -> str:
        return "螺钉"


# =========================
# 装置定义：开放式立体堆叠装置（置物架）
# =========================

@dataclass
class StackedOpenStorageDevice:
    """
    ### 目标：
    定义一种可拆卸组装的开放式的立体堆叠装置，用于增加单位占地面积的存取物品的效率

    说明（直接对应理由）：
    - 实体装置体积：占地面积 + 高度；装置高度 = 层高 * 层数
    - 用于存储的装置考虑最大承载量
    - 通过纵向堆叠提升单位面积存取效率：装置为分层式
    - 可拆卸组装：由有限个零件组成
    - 开放式：对外通道有开口，不能封闭
    - 仅用于存储：无其他限制
    """

    # -------------------------
    # 边界（严格一一对应字段）
    # -------------------------

    max_total_load: Number
    """装置具有一定承载重量限制"""

    per_layer_height_limit: Number
    """装置每层具有一定高度限制"""

    layer_count_range: Range
    """装置层数需要有范围限制"""

    footprint_area_limit: Number
    """装置本身需要占地面积限制"""

    opening_area_range: Range
    """装置对外通道开口面积有范围限制"""

    # -------------------------
    # 分层结构（分层式装置）
    # -------------------------

    layer_height: Number
    """层高（用于高度=层高*层数）"""

    layers: int
    """层数"""

    # -------------------------
    # 零件（一定数量独立的零件构成）
    # -------------------------

    support_columns: List[SupportColumn] = field(default_factory=list)
    plane_boards: List[PlaneBoard] = field(default_factory=list)
    interfaces: List[InterfacePart] = field(default_factory=list)

    # -------------------------
    # 开放式（对外通道开口）
    # -------------------------

    opening_area: Number = 0.0
    """对外通道开口面积（用于范围限制）"""

    # -------------------------
    # 可拆卸组装（组装状态）
    # -------------------------

    assembled: bool = False

    # =========================
    # 派生量：占地面积、高度、体积概念
    # =========================

    @property
    def total_height(self) -> Number:
        """装置的高度则等于层高*层数"""
        return self.layer_height * self.layers

    @property
    def footprint_area(self) -> Number:
        """
        占地面积：
        - 这里以“单层平面板的最大面积”作为占地面积的代表（典型置物架外轮廓）
        - 若未提供平面板，则为 0
        """
        if not self.plane_boards:
            return 0.0
        return max(b.area for b in self.plane_boards)

    @property
    def part_count(self) -> int:
        """装置由一定数量独立的零件构成（数量）"""
        return len(self.support_columns) + len(self.plane_boards) + len(self.interfaces)

    @property
    def surface_area(self) -> Number:
        """
        表面积近似：
        - 用“各层平面板面积之和”近似表面积（用于“增加表面积≈增加LIFO管道”这一解释）
        """
        return sum(b.area for b in self.plane_boards)

    @property
    def efficiency_per_footprint(self) -> Number:
        """
        单位占地面积存取效率（抽象量）：
        - 用“表面积/占地面积”作为单位面积可供存取的表面积倍率
        - 占地面积为 0 时返回 0
        """
        fa = self.footprint_area
        if fa <= 0:
            return 0.0
        return self.surface_area / fa

    # =========================
    # 核心：验证边界 + 组合规则
    # =========================

    def validate(self) -> None:
        """
        边界验证（严格对应“边界”段落）+ 组合规则验证（严格对应“组合规则”）
        """

        # ---- 边界：承载重量限制 ----
        if self.max_total_load <= 0:
            raise ValueError("max_total_load 必须为正数（承载重量限制）")

        # ---- 边界：每层高度限制 ----
        if self.layer_height <= 0:
            raise ValueError("layer_height 必须为正数（层高）")
        if self.per_layer_height_limit <= 0:
            raise ValueError("per_layer_height_limit 必须为正数（每层高度限制）")
        if self.layer_height > self.per_layer_height_limit:
            raise ValueError("layer_height 超过 per_layer_height_limit（每层具有一定高度限制）")

        # ---- 边界：层数范围限制 ----
        if self.layers <= 0:
            raise ValueError("layers 必须为正整数（层数）")
        self.layer_count_range.validate(self.layers, "layers")

        # ---- 边界：占地面积限制 ----
        if self.footprint_area_limit <= 0:
            raise ValueError("footprint_area_limit 必须为正数（占地面积限制）")
        if self.footprint_area > self.footprint_area_limit:
            raise ValueError("footprint_area 超过 footprint_area_limit（装置本身需要占地面积限制）")

        # ---- 边界：开口面积范围限制（开放式）----
        self.opening_area_range.validate(self.opening_area, "opening_area")

        # ---- 零件构成（一定数量独立零件）----
        if self.part_count <= 0:
            raise ValueError("装置必须由零件构成（part_count 不能为 0）")

        # ---- 组合规则：功能与接口 ----
        # 支撑柱、平面板必须是功能；interfaces 必须是接口（类型已体现）
        # 功能与功能之间需要通过接口进行连接：这里要求至少存在接口，且接口链接的对象均为功能
        if not self.interfaces:
            raise ValueError("功能与功能之间需要通过接口进行连接：interfaces 不能为空")

        for itf in self.interfaces:
            itf.validate_links()
            # 确保链接对象均为功能（类型上已是 FunctionalPart，但仍做显式检查）
            for fp in itf.linked_functional_parts:
                if not isinstance(fp, FunctionalPart):
                    raise ValueError("接口链接对象必须为功能（FunctionalPart）")

        # ---- 承载核算（最大承载量）----
        # 这里做一个保守核算：整体最大承载量不得超过“板面承载合计”与“柱轴向承载合计”的较小者
        board_capacity = sum(b.max_surface_load for b in self.plane_boards) if self.plane_boards else 0.0
        column_capacity = sum(c.max_axial_load for c in self.support_columns) if self.support_columns else 0.0
        structural_capacity = min(board_capacity, column_capacity) if (board_capacity > 0 and column_capacity > 0) else 0.0

        if structural_capacity <= 0:
            raise ValueError("承载系统与支撑系统必须具备正的承载能力（平面板/支撑柱承载能力不足）")

        if self.max_total_load > structural_capacity:
            raise ValueError(
                "max_total_load 超过结构可承载能力（考虑最大承载量）："
                f"max_total_load={self.max_total_load}, structural_capacity={structural_capacity}"
            )

    # =========================
    # 可拆卸组装：组装/拆卸
    # =========================

    def assemble(self) -> None:
        """
        可拆卸组装：
        - 组装前进行 validate
        - 标记 assembled=True
        """
        self.validate()
        self.assembled = True

    def disassemble(self) -> None:
        """
        可拆卸组装：
        - 标记 assembled=False
        - 零件列表保留（表示可再次组装）
        """
        self.assembled = False


# =========================
# 一个最小示例（可删除）
# =========================
if __name__ == "__main__":
    # 单层示例：4支撑柱 + 1平面板 + 4接口（每个接口连接“板+柱”）
    cols = [SupportColumn(height=0.5, max_axial_load=200.0) for _ in range(4)]
    board = PlaneBoard(length=0.8, width=0.4, thickness=0.02, max_surface_load=300.0)

    interfaces: List[InterfacePart] = []
    for i in range(4):
        interfaces.append(TenonMortise(_linked=(board, cols[i])))

    device = StackedOpenStorageDevice(
        max_total_load=250.0,
        per_layer_height_limit=1.0,
        layer_count_range=Range(1, 10),
        footprint_area_limit=0.5,  # 0.8*0.4=0.32 <= 0.5
        opening_area_range=Range(0.05, 2.0),
        layer_height=0.5,
        layers=1,
        support_columns=cols,
        plane_boards=[board],
        interfaces=interfaces,
        opening_area=0.2,
    )

    device.assemble()
    print("assembled:", device.assembled)
    print("footprint_area:", device.footprint_area)
    print("total_height:", device.total_height)
    print("part_count:", device.part_count)
    print("efficiency_per_footprint:", device.efficiency_per_footprint)