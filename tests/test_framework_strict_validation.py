from __future__ import annotations

import tempfile
import textwrap
import unittest
from pathlib import Path
from unittest import mock

from scripts import validate_strict_mapping


def build_framework_doc(
    title: str,
    capabilities: list[str],
    boundaries: list[str],
    bases: list[str],
    rules: list[str],
    verifications: list[str],
) -> str:
    return "\n".join(
        [
            f"# {title}",
            "",
            "@framework",
            "",
            "## 1. 能力声明（Capability Statement）",
            "",
            *capabilities,
            "",
            "## 2. 边界定义（Boundary / 参数）",
            "",
            *boundaries,
            "",
            "## 3. 最小可行基（Minimum Viable Bases）",
            "",
            *bases,
            "",
            "## 4. 基组合原则（Base Combination Principles）",
            "",
            *rules,
            "",
            "## 5. 验证（Verification）",
            "",
            *verifications,
            "",
        ]
    )


class FrameworkStrictValidationTest(unittest.TestCase):
    def run_framework_validation(self, files: dict[str, str]) -> list[dict[str, object]]:
        with tempfile.TemporaryDirectory(dir=validate_strict_mapping.REPO_ROOT) as tmp_dir:
            framework_dir = Path(tmp_dir) / "framework"
            for rel_path, content in files.items():
                file_path = framework_dir / rel_path
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text(textwrap.dedent(content).strip() + "\n", encoding="utf-8")

            with mock.patch.object(validate_strict_mapping, "FRAMEWORK_DIR", framework_dir):
                issues, _ = validate_strict_mapping.validate_framework_layers()
            return issues

    def test_capability_must_not_map_to_multiple_base_sources(self) -> None:
        issues = self.run_framework_validation(
            {
                "demo/L0-M0-能力归属模块.md": build_framework_doc(
                    "能力归属模块:CapabilityOwnershipModule",
                    [
                        "- `C1` 承载能力：定义稳定承载结构。",
                        "- `C2` 治理能力：定义治理闭环。",
                        "- `N1` 非职责声明：不负责实例参数。",
                    ],
                    [
                        "- `P1` 参数一：承载边界。来源：`C1`。",
                        "- `P2` 参数二：治理边界。来源：`C2`。",
                    ],
                    [
                        "- `B1` 承载结构基：由承载骨架组成。来源：`C1 + P1`。",
                        "- `B2` 治理结构基：由治理节点组成。来源：`C1 + C2 + P2`。",
                    ],
                    [
                        "- `R1` 承载组合",
                        "  - `R1.1` 参与基：`B1`。",
                        "  - `R1.2` 组合方式：固定承载骨架。",
                        "  - `R1.3` 输出能力：`C1`。",
                        "  - `R1.4` 边界绑定：`P1`。",
                        "- `R2` 治理组合",
                        "  - `R2.1` 参与基：`B2`。",
                        "  - `R2.2` 组合方式：挂接治理节点。",
                        "  - `R2.3` 输出能力：`C2`。",
                        "  - `R2.4` 边界绑定：`P2`。",
                    ],
                    [
                        "- `V1` 能力归属必须唯一。",
                    ],
                )
            }
        )
        self.assertTrue(any(issue["code"] == "FW075" for issue in issues))

    def test_support_only_base_may_omit_capability_token(self) -> None:
        issues = self.run_framework_validation(
            {
                "demo/L0-M0-支撑模块.md": build_framework_doc(
                    "支撑模块:SupportOnlyBaseModule",
                    [
                        "- `C1` 承载能力：定义稳定承载结构。",
                        "- `N1` 非职责声明：不负责实例参数。",
                    ],
                    [
                        "- `P1` 参数一：承载边界。来源：`C1`。",
                        "- `P2` 参数二：支撑边界。来源：`C1`。",
                    ],
                    [
                        "- `B1` 承载结构基：由承载骨架组成。来源：`C1 + P1`。",
                        "- `B2` 支撑结构基：由辅助连接点组成。来源：`P2`。",
                    ],
                    [
                        "- `R1` 支撑组合",
                        "  - `R1.1` 参与基：`B1 + B2`。",
                        "  - `R1.2` 组合方式：用支撑结构稳定承载骨架。",
                        "  - `R1.3` 输出能力：`C1`。",
                        "  - `R1.4` 边界绑定：`P1 + P2`。",
                    ],
                    [
                        "- `V1` 支撑结构必须参与组合。",
                    ],
                )
            }
        )
        self.assertFalse(any(issue["code"] in {"FW022", "FW070", "FW075"} for issue in issues))

    def test_non_l0_base_requires_inline_adjacent_module_refs(self) -> None:
        issues = self.run_framework_validation(
            {
                "demo/L0-M0-底座模块.md": build_framework_doc(
                    "底座模块:FoundationModule",
                    [
                        "- `C1` 结构能力：定义稳定结构。",
                        "- `C2` 承载能力：定义承载关系。",
                        "- `C3` 扩展能力：允许上层展开。",
                        "- `N1` 非职责声明：不负责上层组合。",
                    ],
                    [
                        "- `P1` 参数一：结构边界。来源：`C1`。",
                        "- `P2` 参数二：承载边界。来源：`C1 + C2`。",
                    ],
                    [
                        "- `B1` 根结构基：由骨架与接口组成。来源：`C1 + P1`。",
                    ],
                    [
                        "- `R1` 根结构组合",
                        "  - `R1.1` 参与基：`B1`。",
                        "  - `R1.2` 组合方式：固定根层结构与接口边界。",
                        "  - `R1.3` 输出能力：`C1 + C2`。",
                        "  - `R1.4` 边界绑定：`P1 + P2`。",
                    ],
                    [
                        "- `V1` 根层结构必须可独立成立。",
                    ],
                ),
                "demo/L1-M0-上层模块.md": build_framework_doc(
                    "上层模块:UpperModule",
                    [
                        "- `C1` 上层能力：组织下层结构。",
                        "- `C2` 编排能力：约束组合路径。",
                        "- `C3` 扩展能力：支持继续生长。",
                        "- `N1` 非职责声明：不负责实例配置。",
                    ],
                    [
                        "- `P1` 参数一：组合边界。来源：`C1 + C2`。",
                        "- `P2` 参数二：扩展边界。来源：`C2 + C3`。",
                    ],
                    [
                        "- `B1` 上层结构基：由骨架收敛而成。来源：`C1 + P1`。",
                    ],
                    [
                        "- `R1` 上层组合",
                        "  - `R1.1` 参与基：`B1`。",
                        "  - `R1.2` 组合方式：按相邻层规则收敛结构。",
                        "  - `R1.3` 输出能力：`C1 + C2`。",
                        "  - `R1.4` 边界绑定：`P1 + P2`。",
                    ],
                    [
                        "- `V1` 上层结构必须可回溯到下层输入。",
                    ],
                ),
            }
        )
        self.assertTrue(any(issue["code"] == "FW024" for issue in issues))

    def test_inline_ref_must_point_to_existing_adjacent_module(self) -> None:
        issues = self.run_framework_validation(
            {
                "demo/L0-M0-底座模块.md": build_framework_doc(
                    "底座模块:FoundationModule",
                    [
                        "- `C1` 结构能力：定义稳定结构。",
                        "- `C2` 承载能力：定义承载关系。",
                        "- `C3` 扩展能力：允许上层展开。",
                        "- `N1` 非职责声明：不负责上层组合。",
                    ],
                    [
                        "- `P1` 参数一：结构边界。来源：`C1`。",
                        "- `P2` 参数二：承载边界。来源：`C1 + C2`。",
                    ],
                    [
                        "- `B1` 根结构基：由骨架与接口组成。来源：`C1 + P1`。",
                    ],
                    [
                        "- `R1` 根结构组合",
                        "  - `R1.1` 参与基：`B1`。",
                        "  - `R1.2` 组合方式：固定根层结构与接口边界。",
                        "  - `R1.3` 输出能力：`C1 + C2`。",
                        "  - `R1.4` 边界绑定：`P1 + P2`。",
                    ],
                    [
                        "- `V1` 根层结构必须可独立成立。",
                    ],
                ),
                "demo/L1-M0-上层模块.md": build_framework_doc(
                    "上层模块:UpperModule",
                    [
                        "- `C1` 上层能力：组织下层结构。",
                        "- `C2` 编排能力：约束组合路径。",
                        "- `C3` 扩展能力：支持继续生长。",
                        "- `N1` 非职责声明：不负责实例配置。",
                    ],
                    [
                        "- `P1` 参数一：组合边界。来源：`C1 + C2`。",
                        "- `P2` 参数二：扩展边界。来源：`C2 + C3`。",
                    ],
                    [
                        "- `B1` 上层结构基：L0.M1[R1]。来源：`C1 + P1`。",
                    ],
                    [
                        "- `R1` 上层组合",
                        "  - `R1.1` 参与基：`B1`。",
                        "  - `R1.2` 组合方式：按相邻层规则收敛结构。",
                        "  - `R1.3` 输出能力：`C1 + C2`。",
                        "  - `R1.4` 边界绑定：`P1 + P2`。",
                    ],
                    [
                        "- `V1` 上层结构必须可回溯到下层输入。",
                    ],
                ),
            }
        )
        self.assertTrue(any(issue["code"] == "FW025" for issue in issues))

    def test_l0_base_cannot_reference_upstream_module(self) -> None:
        issues = self.run_framework_validation(
            {
                "demo/L0-M0-底座模块.md": build_framework_doc(
                    "底座模块:FoundationModule",
                    [
                        "- `C1` 结构能力：定义稳定结构。",
                        "- `C2` 承载能力：定义承载关系。",
                        "- `C3` 扩展能力：允许上层展开。",
                        "- `N1` 非职责声明：不负责上层组合。",
                    ],
                    [
                        "- `P1` 参数一：结构边界。来源：`C1`。",
                        "- `P2` 参数二：承载边界。来源：`C1 + C2`。",
                    ],
                    [
                        "- `B1` 根结构基：L0.M1[R1]。来源：`C1 + P1`。",
                    ],
                    [
                        "- `R1` 根结构组合",
                        "  - `R1.1` 参与基：`B1`。",
                        "  - `R1.2` 组合方式：固定根层结构与接口边界。",
                        "  - `R1.3` 输出能力：`C1 + C2`。",
                        "  - `R1.4` 边界绑定：`P1 + P2`。",
                    ],
                    [
                        "- `V1` 根层结构必须可独立成立。",
                    ],
                ),
                "demo/L0-M1-附属模块.md": build_framework_doc(
                    "附属模块:AuxModule",
                    [
                        "- `C1` 辅助能力：提供补充结构。",
                        "- `C2` 承载能力：提供承载关系。",
                        "- `C3` 扩展能力：允许上层展开。",
                        "- `N1` 非职责声明：不负责上层组合。",
                    ],
                    [
                        "- `P1` 参数一：结构边界。来源：`C1`。",
                        "- `P2` 参数二：承载边界。来源：`C1 + C2`。",
                    ],
                    [
                        "- `B1` 辅助结构基：由补充接口组成。来源：`C1 + P1`。",
                    ],
                    [
                        "- `R1` 辅助组合",
                        "  - `R1.1` 参与基：`B1`。",
                        "  - `R1.2` 组合方式：固定辅助结构与接口边界。",
                        "  - `R1.3` 输出能力：`C1 + C2`。",
                        "  - `R1.4` 边界绑定：`P1 + P2`。",
                    ],
                    [
                        "- `V1` 辅助结构必须可独立成立。",
                    ],
                ),
            }
        )
        self.assertTrue(any(issue["code"] == "FW026" for issue in issues))

    def test_l0_base_can_reference_external_foundation_module(self) -> None:
        issues = self.run_framework_validation(
            {
                "frontend/L0-M0-运行底座模块.md": build_framework_doc(
                    "运行底座模块:RuntimeFoundation",
                    [
                        "- `C1` 运行能力：定义运行壳。",
                        "- `C2` 承载能力：定义挂载关系。",
                        "- `C3` 治理能力：定义治理约束。",
                        "- `N1` 非职责声明：不负责领域语义。",
                    ],
                    [
                        "- `P1` 参数一：平台边界。来源：`C1 + C3`。",
                        "- `P2` 参数二：挂载边界。来源：`C1 + C2`。",
                    ],
                    [
                        "- `B1` 运行壳结构基：由根容器和入口组成。来源：`C1 + P1`。",
                    ],
                    [
                        "- `R1` 运行组合",
                        "  - `R1.1` 参与基：`B1`。",
                        "  - `R1.2` 组合方式：固定运行壳和挂载入口。",
                        "  - `R1.3` 输出能力：`C1 + C2`。",
                        "  - `R1.4` 边界绑定：`P1 + P2`。",
                    ],
                    [
                        "- `V1` 运行壳必须独立成立。",
                    ],
                ),
                "frontend/L1-M0-通用组件模块.md": build_framework_doc(
                    "通用组件模块:GenericComponents",
                    [
                        "- `C1` 原子能力：定义输入与展示原子。",
                        "- `C2` 契约能力：定义组件契约。",
                        "- `C3` 扩展能力：支持领域承接。",
                        "- `N1` 非职责声明：不负责领域对象。",
                    ],
                    [
                        "- `P1` 参数一：组件边界。来源：`C1 + C2`。",
                        "- `P2` 参数二：扩展边界。来源：`C2 + C3`。",
                    ],
                    [
                        "- `B1` 组件结构基：L0.M0[R1]。来源：`C1 + P1`。",
                    ],
                    [
                        "- `R1` 组件组合",
                        "  - `R1.1` 参与基：`B1`。",
                        "  - `R1.2` 组合方式：用运行底座承接基础组件。",
                        "  - `R1.3` 输出能力：`C1 + C2`。",
                        "  - `R1.4` 边界绑定：`P1 + P2`。",
                    ],
                    [
                        "- `V1` 组件必须可由底座承接。",
                    ],
                ),
                "knowledge_base/L0-M0-文件库模块.md": build_framework_doc(
                    "文件库模块:KnowledgeFileLibrary",
                    [
                        "- `C1` 目录能力：定义文件目录结构。",
                        "- `C2` 摄取能力：定义文件摄取结构。",
                        "- `C3` 治理能力：定义目录约束。",
                        "- `N1` 非职责声明：不负责对话引用。",
                    ],
                    [
                        "- `P1` 参数一：文件集边界。来源：`C1 + C3`。",
                        "- `P2` 参数二：摄取边界。来源：`C2 + C3`。",
                    ],
                    [
                        "- `B1` 文件目录结构基：frontend.L0.M0[R1]。来源：`C1 + P1`。",
                    ],
                    [
                        "- `R1` 文件库组合",
                        "  - `R1.1` 参与基：`B1`。",
                        "  - `R1.2` 组合方式：由前端基础组件承接文件目录结构。",
                        "  - `R1.3` 输出能力：`C1 + C2`。",
                        "  - `R1.4` 边界绑定：`P1 + P2`。",
                    ],
                    [
                        "- `V1` 文件目录结构必须可回溯到前端基础组件。",
                    ],
                ),
            }
        )
        self.assertFalse(any(issue["code"] in {"FW026", "FW027", "FW028"} for issue in issues))

    def test_l0_external_foundation_ref_must_exist(self) -> None:
        issues = self.run_framework_validation(
            {
                "knowledge_base/L0-M0-文件库模块.md": build_framework_doc(
                    "文件库模块:KnowledgeFileLibrary",
                    [
                        "- `C1` 目录能力：定义文件目录结构。",
                        "- `C2` 摄取能力：定义文件摄取结构。",
                        "- `C3` 治理能力：定义目录约束。",
                        "- `N1` 非职责声明：不负责对话引用。",
                    ],
                    [
                        "- `P1` 参数一：文件集边界。来源：`C1 + C3`。",
                        "- `P2` 参数二：摄取边界。来源：`C2 + C3`。",
                    ],
                    [
                        "- `B1` 文件目录结构基：frontend.L1.M9[R1]。来源：`C1 + P1`。",
                    ],
                    [
                        "- `R1` 文件库组合",
                        "  - `R1.1` 参与基：`B1`。",
                        "  - `R1.2` 组合方式：由前端基础组件承接文件目录结构。",
                        "  - `R1.3` 输出能力：`C1 + C2`。",
                        "  - `R1.4` 边界绑定：`P1 + P2`。",
                    ],
                    [
                        "- `V1` 文件目录结构必须可回溯到前端基础组件。",
                    ],
                ),
            }
        )
        self.assertTrue(any(issue["code"] == "FW028" for issue in issues))

    def test_non_l0_base_still_requires_local_adjacent_ref(self) -> None:
        issues = self.run_framework_validation(
            {
                "frontend/L0-M0-运行底座模块.md": build_framework_doc(
                    "运行底座模块:RuntimeFoundation",
                    [
                        "- `C1` 运行能力：定义运行壳。",
                        "- `C2` 承载能力：定义挂载关系。",
                        "- `C3` 治理能力：定义治理约束。",
                        "- `N1` 非职责声明：不负责领域语义。",
                    ],
                    [
                        "- `P1` 参数一：平台边界。来源：`C1 + C3`。",
                        "- `P2` 参数二：挂载边界。来源：`C1 + C2`。",
                    ],
                    [
                        "- `B1` 运行壳结构基：由根容器和入口组成。来源：`C1 + P1`。",
                    ],
                    [
                        "- `R1` 运行组合",
                        "  - `R1.1` 参与基：`B1`。",
                        "  - `R1.2` 组合方式：固定运行壳和挂载入口。",
                        "  - `R1.3` 输出能力：`C1 + C2`。",
                        "  - `R1.4` 边界绑定：`P1 + P2`。",
                    ],
                    [
                        "- `V1` 运行壳必须独立成立。",
                    ],
                ),
                "frontend/L1-M0-通用组件模块.md": build_framework_doc(
                    "通用组件模块:GenericComponents",
                    [
                        "- `C1` 原子能力：定义输入与展示原子。",
                        "- `C2` 契约能力：定义组件契约。",
                        "- `C3` 扩展能力：支持领域承接。",
                        "- `N1` 非职责声明：不负责领域对象。",
                    ],
                    [
                        "- `P1` 参数一：组件边界。来源：`C1 + C2`。",
                        "- `P2` 参数二：扩展边界。来源：`C2 + C3`。",
                    ],
                    [
                        "- `B1` 组件结构基：L0.M0[R1]。来源：`C1 + P1`。",
                    ],
                    [
                        "- `R1` 组件组合",
                        "  - `R1.1` 参与基：`B1`。",
                        "  - `R1.2` 组合方式：用运行底座承接基础组件。",
                        "  - `R1.3` 输出能力：`C1 + C2`。",
                        "  - `R1.4` 边界绑定：`P1 + P2`。",
                    ],
                    [
                        "- `V1` 组件必须可由底座承接。",
                    ],
                ),
                "knowledge_base/L0-M0-文件库模块.md": build_framework_doc(
                    "文件库模块:KnowledgeFileLibrary",
                    [
                        "- `C1` 目录能力：定义文件目录结构。",
                        "- `C2` 摄取能力：定义文件摄取结构。",
                        "- `C3` 治理能力：定义目录约束。",
                        "- `N1` 非职责声明：不负责对话引用。",
                    ],
                    [
                        "- `P1` 参数一：文件集边界。来源：`C1 + C3`。",
                        "- `P2` 参数二：摄取边界。来源：`C2 + C3`。",
                    ],
                    [
                        "- `B1` 文件目录结构基：frontend.L0.M0[R1]。来源：`C1 + P1`。",
                    ],
                    [
                        "- `R1` 文件库组合",
                        "  - `R1.1` 参与基：`B1`。",
                        "  - `R1.2` 组合方式：由前端基础组件承接文件目录结构。",
                        "  - `R1.3` 输出能力：`C1 + C2`。",
                        "  - `R1.4` 边界绑定：`P1 + P2`。",
                    ],
                    [
                        "- `V1` 文件目录结构必须可回溯到前端基础组件。",
                    ],
                ),
                "knowledge_base/L1-M0-界面骨架模块.md": build_framework_doc(
                    "界面骨架模块:WorkbenchSkeleton",
                    [
                        "- `C1` 骨架能力：定义工作台骨架。",
                        "- `C2` 联动能力：定义多区联动。",
                        "- `C3` 复用能力：支持响应式复用。",
                        "- `N1` 非职责声明：不负责项目实例。",
                    ],
                    [
                        "- `P1` 参数一：区域边界。来源：`C1 + C2`。",
                        "- `P2` 参数二：响应式边界。来源：`C2 + C3`。",
                    ],
                    [
                        "- `B1` 骨架结构基：frontend.L0.M0[R1]。来源：`C1 + P1`。",
                    ],
                    [
                        "- `R1` 骨架组合",
                        "  - `R1.1` 参与基：`B1`。",
                        "  - `R1.2` 组合方式：用前端基础组件承接骨架结构。",
                        "  - `R1.3` 输出能力：`C1 + C2`。",
                        "  - `R1.4` 边界绑定：`P1 + P2`。",
                    ],
                    [
                        "- `V1` 骨架结构必须可回溯到下层输入。",
                    ],
                ),
            }
        )
        self.assertTrue(any(issue["code"] == "FW024" for issue in issues))

    def test_negative_rule_uses_invalid_conclusion_instead_of_output_capability(self) -> None:
        issues = self.run_framework_validation(
            {
                "demo/L0-M0-负向规则模块.md": build_framework_doc(
                    "负向规则模块:NegativeRuleModule",
                    [
                        "- `C1` 承载能力：定义稳定承载结构。",
                        "- `C2` 组合能力：定义合法组合关系。",
                        "- `N1` 非职责声明：不负责实例配置。",
                    ],
                    [
                        "- `P1` 参数一：承载边界。来源：`C1`。",
                        "- `P2` 参数二：组合边界。来源：`C1 + C2`。",
                    ],
                    [
                        "- `B1` 承载结构基：由承载骨架组成。来源：`C1 + P1`。",
                        "- `B2` 组合结构基：由组合关系组成。来源：`C2 + P2`。",
                    ],
                    [
                        "- `R1` 合法组合",
                        "  - `R1.1` 参与基：`B1 + B2`。",
                        "  - `R1.2` 组合方式：固定承载关系后闭合组合。",
                        "  - `R1.3` 输出能力：`C1 + C2`。",
                        "  - `R1.4` 边界绑定：`P1 + P2`。",
                        "- `R2` 禁止组合",
                        "  - `R2.1` 参与基：`B1 + B2`。",
                        "  - `R2.2` 组合方式：绕过边界约束的组合均无效。",
                        "  - `R2.3` 失效结论：`N1`。",
                        "  - `R2.4` 边界绑定：`P1 + P2`。",
                    ],
                    [
                        "- `V1` 合法组合与禁止组合必须可区分。",
                    ],
                ),
            }
        )
        self.assertFalse(any(issue["code"] in {"FW041", "FW050", "FW051", "FW052"} for issue in issues))

    def test_negative_rule_must_not_write_non_responsibility_into_output_capability(self) -> None:
        issues = self.run_framework_validation(
            {
                "demo/L0-M0-错误负向规则模块.md": build_framework_doc(
                    "错误负向规则模块:InvalidNegativeRuleModule",
                    [
                        "- `C1` 承载能力：定义稳定承载结构。",
                        "- `C2` 组合能力：定义合法组合关系。",
                        "- `N1` 非职责声明：不负责实例配置。",
                    ],
                    [
                        "- `P1` 参数一：承载边界。来源：`C1`。",
                        "- `P2` 参数二：组合边界。来源：`C1 + C2`。",
                    ],
                    [
                        "- `B1` 承载结构基：由承载骨架组成。来源：`C1 + P1`。",
                        "- `B2` 组合结构基：由组合关系组成。来源：`C2 + P2`。",
                    ],
                    [
                        "- `R1` 禁止组合",
                        "  - `R1.1` 参与基：`B1 + B2`。",
                        "  - `R1.2` 组合方式：绕过边界约束的组合均无效。",
                        "  - `R1.3` 输出能力：`N1`。",
                        "  - `R1.4` 边界绑定：`P1 + P2`。",
                    ],
                    [
                        "- `V1` 禁止组合必须有独立负向结论。",
                    ],
                ),
            }
        )
        self.assertTrue(any(issue["code"] in {"FW041", "FW050", "FW052"} for issue in issues))


if __name__ == "__main__":
    unittest.main()
