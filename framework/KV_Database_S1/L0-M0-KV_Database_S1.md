# KV数据库:KVDatabase
<!-- 这是一个内存版KV数据库的框架，只实现了内存版KV数据库（数据不落盘保存），以及WAL功能（日志编写+程序运行时恢复数据）-->
@framework

## 1. 能力声明（Capability Statement）

- `C1` 数据存储的能力：能存储KEY值和VALUE值。
- `C2` 数据映射的能力：能建立KEY值和VALUE值之间的映射关系，每个KEY有且只有一个映射的VALUE，且这个映射关系是正向的（只能从KEY到VALUE）。
- `C3` 数据查找的能力：能根据KEY值查找其映射的VALUE值。
- `C4` 数据删除的能力：能删除KEY值和其映射的VALUE值。
- `C5` 日志编写的能力：每次对数据进行存储、删除的时候将具体操作和对应的KEY，VALUE值写入日志。
- `C6` 数据恢复的能力：每次运行程序的时候能根据日志恢复之前的KV数据库。

### 非职责声明（Non-Responsibility Statement）

- `N1` 非职责声明：不考虑并发处理，不考虑高效查询。

## 2. 边界定义（Boundary / 参数）

- `OPERATION` 操作边界：对数据的操作只能是"put"，"get"，"delete"。来源：`C1 + C3 + C4`。
- `KEY` KEY边界：每次操作必须输入一个KEY，且是str类型。来源：`C1 + C2 + C3 + C4`。
- `VALUE` VALUE边界：操作必须输入一个VALUE，不限数据类型。来源：`C1 + C2 + C3 + C4`。
- `PATH` 路径边界：日志存放的路径，和日志文件名必须明确。来源`C5 + C6`。
- `LOG` 日志内容边界：日志以"操作"，"KEY"，"VALUE"的格式进行排列。来源`C5 + C6`。

## 3. 最小可行基（Minimum Viable Bases）

- `B1` 字典：python自带的dict。来源：`C1 + C2 + C3 + C4 + OPERATION + KEY + VALUE`。
- `B2` 日志：记录"操作"，"KEY"，"VALUE"内容。来源：`C5 + C6 + PATH + LOG`


## 4. 基组合原则（Base Combination Principles）

- `R1` 数据存储组合
  - `R1.1` 参与基：`B1 + B2`。
  - `R1.2` 组合方式：在进行"put"操作的时候，先将操作和对应的KEY，VALUE写入日志，然后再对字典进行操作。
  - `R1.3` 输出能力：`C1 + C2 + C5`。
  - `R1.4` 边界绑定：`OPERATION + KEY + VALUE + PATH + LOG`。
- `R2` 数据查询组合
  - `R2.1` 参与基：`B1`。
  - `R2.2` 组合方式：在进行"get"操作的时候，根据KEY查询对应的VALUE并返回，若在数据库中没有找到KEY，则raise KeyError。
  - `R2.3` 输出能力：`C3`。
  - `R2.4` 边界绑定：`OPERATION + KEY + VALUE`。
- `R3` 数据删除组合
  - `R3.1` 参与基：`B1 + B2`。
  - `R3.2` 组合方式：在进行"delete"操作的时候，先将操作和对应的KEY，VALUE写入日志，然后根据KEY查询对应的VALUE并返回、然后删除，若在数据库中没有找到KEY，则raise KeyError。
  - `R3.3` 输出能力：`C4 + C5`。
  - `R3.4` 边界绑定：`OPERATION + KEY + VALUE + PATH + LOG`。
- `R4` 数据恢复组合
  - `R4.1` 参与基：`B1 + B2`。
  - `R4.2` 组合方式：在程序运行的时候，从日志里获取之前执行过的操作，并恢复其中的数据。
  - `R4.3` 输出能力：`C6`。
  - `R4.4` 边界绑定：`OPERATION + KEY + VALUE + PATH + LOG`。


## 5. 验证（Verification）

- `V1` 操作正确性：数据库内容变化，必须与执行的操作、输入的KEY和VALUE一致，
- `V2` 操作、日志一致性：内存中维护的数据库必须与通过日志恢复的数据库一致。
- `V3` 结构闭环性：`R1~R4` 输出能力并集必须覆盖 `C1~C6`。
- `V4` 边界符合性：所有有效组合必须满足绑定的参数边界。
- `V5` 最小必要性：移除任一 `B*` 后，`V3` 或 `V4` 至少一项失败。
- `V6` 结论表达：逐条输出 `R* -> C* + 边界绑定` 或 `R* -> N* + 边界绑定` 的通过或失败结论。