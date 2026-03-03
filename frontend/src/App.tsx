import React, { useState, useMemo } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, Box, Edges, Environment, ContactShadows } from '@react-three/drei';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { LayoutDashboard, CheckCircle2, XCircle, Grid, Box as BoxIcon, Info } from 'lucide-react';

type ModuleType = 'v_rod' | 'h_rod' | 'connector' | 'panel';

interface LayoutItem {
  id: string;
  group: '单元模块边界测试' | '2x2平层阵列组合';
  name: string;
  mode: 'module' | 'grid';
  modules?: { type: ModuleType; count: number }[];
  gridLayers?: number[];
  valid: boolean;
  reason: string;
  vRods: number;
  hRods: number;
  connectors: number;
  panels: number;
}

const combinationsDef = [
  // 零散组合 (不合规)
  { name: '单根竖杆', modules: [{ type: 'v_rod', count: 1 }] },
  { name: '单连接件', modules: [{ type: 'connector', count: 1 }] },
  { name: '两板+连接件', modules: [{ type: 'panel', count: 2 }, { type: 'connector', count: 1 }] },
  
  // 规模 4 (单层 1置物架 - 不合规边界)
  { name: '单层: 单侧支撑(2竖+2横+1板+2口)', modules: [{ type: 'v_rod', count: 2 }, { type: 'h_rod', count: 2 }, { type: 'panel', count: 1 }, { type: 'connector', count: 2 }] },
  { name: '单层: 缺竖板(4横+1板+4口)', modules: [{ type: 'h_rod', count: 4 }, { type: 'panel', count: 1 }, { type: 'connector', count: 4 }] },
  
  // R5 标准闭环 (合规, 但作为整体单位面积评估可能受 R6 限制，不过此处为纯单元测试所以保留放行)
  { name: '单层: 完整闭环(4竖+4横+4接口+1板)', modules: [{ type: 'v_rod', count: 4 }, { type: 'h_rod', count: 4 }, { type: 'panel', count: 1 }, { type: 'connector', count: 4 }] }
];

const generateAllCombos = (): LayoutItem[] => {
  const items: LayoutItem[] = [];
  
  // 1. 生成单元模块测试数据 (底层框架组件验证)
  combinationsDef.forEach((def, idx) => {
    const getCount = (t: ModuleType) => def.modules.find(m => m.type === t)?.count || 0;
    const vRods = getCount('v_rod'), hRods = getCount('h_rod'), connectors = getCount('connector'), panels = getCount('panel');
    const totalModules = vRods + hRods + connectors + panels;

    const r1 = totalModules >= 2;
    const r2 = connectors >= 1;
    const r5 = vRods >= 4 && connectors >= 4 && panels >= 1 && hRods >= 4;
    
    let valid = true;
    let reason = '';

    if (!r1) {
      valid = false; reason = '【违反R1】: 孤立模块，数量需 >= 2';
    } else if (!r2) {
      valid = false; reason = '【违反R2】: 未包含连接接口(Connector)';
    } else if (!r5) {
      valid = false; reason = `【违反R5】: 置物架基础组合不完整，需至少 4竖 + 4横 + 4接口 + 1板 闭环`;
    } else {
      valid = true; reason = `满足基础准则: 构建最小闭环置物架 (注意此时如需计算单位面积效率,还需受R6约束)`;
    }

    items.push({
      id: `m_${idx}`, group: '单元模块边界测试', name: def.name, mode: 'module',
      modules: def.modules as { type: ModuleType; count: number }[],
      valid, reason, vRods, hRods, connectors, panels
    });
  });

  // 2. 生成 2x2 平层阵列的组合数据 (包含 R6 层数拦截逻辑验证)
  // 我们穷举 15 种二维占位，同时分别给出 1层高度(报错阻拦) 和 带2层高度(合法) 两种状态
  for (const maxLayerTest of [1, 2, 3]) {
    for(let i=1; i<16; i++) {
        const grid = [
          (i & 1) > 0, // 0: (0,0)
          (i & 2) > 0, // 1: (1,0)
          (i & 4) > 0, // 2: (0,1)
          (i & 8) > 0  // 3: (1,1)
        ];

        // 让激活的第一个地块达到测试层数 maxLayerTest，其他激活的只是1层
        const firstActiveIndex = grid.findIndex(Boolean);
        const layers = grid.map((active, idx) => {
            if (!active) return 0;
            return idx === firstActiveIndex ? maxLayerTest : 1;
        });

        const blockCount = grid.filter(Boolean).length;
        
        let totalVRods = 0, totalHRods = 0, totalConnectors = 0, totalPanels = 0;
        const maxL = Math.max(...layers);
        
        // 逐层累计材料，实现复用计算
        for (let l = 0; l < maxL; l++) {
          const activeAtLevel = layers.map(h => h > l);
          if (!activeAtLevel.some(Boolean)) continue;
          
          const vertices = new Set<string>();
          const hEdges = new Set<string>();
          const cells = [
            { x: 0, z: 0, active: activeAtLevel[0] },
            { x: 1, z: 0, active: activeAtLevel[1] },
            { x: 0, z: 1, active: activeAtLevel[2] },
            { x: 1, z: 1, active: activeAtLevel[3] },
          ];

          cells.forEach(c => {
            if (!c.active) return;
            vertices.add(`${c.x},${c.z}`);
            vertices.add(`${c.x+1},${c.z}`);
            vertices.add(`${c.x},${c.z+1}`);
            vertices.add(`${c.x+1},${c.z+1}`);
            
            hEdges.add(`x_${c.x}_${c.z}`);
            hEdges.add(`x_${c.x}_${c.z+1}`);
            hEdges.add(`z_${c.x}_${c.z}`);
            hEdges.add(`z_${c.x+1}_${c.z}`);
          });

          totalVRods += vertices.size;
          totalHRods += hEdges.size;
          totalConnectors += vertices.size; 
          totalPanels += activeAtLevel.filter(Boolean).length;
        }

        const r6 = maxL >= 2;
        let valid = r6;
        let reason = '';
        if (!r6) {
           reason = "【拦截:违反R6】单位面积内最高只有1层，不满足提升空间存取效率的规划要求。必须>=2层。";
        } else {
           reason = `【通过R6】: 成功布置 ${blockCount}个底座，且包含高达 ${maxL} 层骨架，${blockCount>1?'相邻接触面发生材料复用。':'独立运作。'}`;
        }

        // 仅挑选部分代表性数据防止 UI 爆炸
        // 在 maxLayer=1 下选 3 种典型，maxLayer=2,3 下全量或部分
        if (maxLayerTest === 1 && ![1, 3, 15].includes(i)) continue;
        if (maxLayerTest === 3 && i !== 15) continue; 

        items.push({
          id: `g_${maxLayerTest}_${i}`,
          group: '2x2平层阵列组合',
          name: `${blockCount}占地 / 最高${maxLayerTest}层`,
          mode: 'grid', gridLayers: layers,
          valid, reason,
          vRods: totalVRods, hRods: totalHRods, connectors: totalConnectors, panels: totalPanels
        });
    }
  }

  return items;
};

// --- Renderers ---

const GridModel = ({ layers }: { layers: number[] }) => {
  const maxL = Math.max(...layers);
  return (
    <group position={[-1.0, -0.5, -1.0]}>
      {Array.from({ length: maxL }).map((_, l) => {
         const activeAtLevel = layers.map(h => h > l);
         if (!activeAtLevel.some(Boolean)) return null;

         const vSet = new Set<string>();
         const hSet = new Set<string>();
         const panelList: {x:number, z:number}[] = [];

         const cells = [
           { x: 0, z: 0, active: activeAtLevel[0] }, { x: 1, z: 0, active: activeAtLevel[1] },
           { x: 0, z: 1, active: activeAtLevel[2] }, { x: 1, z: 1, active: activeAtLevel[3] },
         ];

         cells.forEach(c => {
           if(!c.active) return;
           vSet.add(`${c.x},${c.z}`); vSet.add(`${c.x+1},${c.z}`);
           vSet.add(`${c.x},${c.z+1}`); vSet.add(`${c.x+1},${c.z+1}`);
           hSet.add(`x_${c.x}_${c.z}`); hSet.add(`x_${c.x}_${c.z+1}`);
           hSet.add(`z_${c.x}_${c.z}`); hSet.add(`z_${c.x+1}_${c.z}`);
           panelList.push({ x: c.x, z: c.z });
         });

         const yBase = l * 1.05;

         return (
           <group key={`level_${l}`} position={[0, yBase, 0]}>
             {Array.from(vSet).map(v => {
                const [x, z] = v.split(',').map(Number);
                return (
                  <group key={`v_${v}`}>
                     <Box args={[0.06, 1, 0.06]} position={[x, 0.5, z]}><meshStandardMaterial color="#334155" metalness={0.6} /></Box>
                     <mesh position={[x, 1.0, z]}><sphereGeometry args={[0.08]} /><meshStandardMaterial color="#0f172a" /></mesh>
                  </group>
                )
             })}
             {Array.from(hSet).map(h => {
                 const [axis, xStr, zStr] = h.split('_');
                 const x = Number(xStr), z = Number(zStr);
                 if (axis === 'x') {
                    return <Box key={`h_${h}`} args={[1, 0.06, 0.06]} position={[x + 0.5, 1.0, z]}><meshStandardMaterial color="#334155" metalness={0.6} /></Box>
                 } else {
                    return <Box key={`h_${h}`} args={[0.06, 0.06, 1]} position={[x, 1.0, z + 0.5]}><meshStandardMaterial color="#334155" metalness={0.6} /></Box>
                 }
             })}
             {panelList.map((p, i) => (
                 <Box key={`p_${i}`} args={[0.96, 0.04, 0.96]} position={[p.x + 0.5, 1.05, p.z + 0.5]}>
                     <meshStandardMaterial color="#f8fafc" metalness={0.1} />
                     <Edges color="#cbd5e1" />
                 </Box>
             ))}
           </group>
         );
      })}
    </group>
  );
};

const ModuleModel = ({ modules }: { modules: { type: ModuleType; count: number }[] }) => {
  const getCount = (t: ModuleType) => modules.find(m => m.type === t)?.count || 0;
  const vRods = getCount('v_rod'), hRods = getCount('h_rod'), connectors = getCount('connector'), panels = getCount('panel');
  const total = modules.reduce((a, b) => a + b.count, 0);
  const isStructuralLayout = connectors > 0 && total > 2;
  const positions = [[-0.5, 0.5], [0.5, 0.5], [0.5, -0.5], [-0.5, -0.5]];

  return (
    <group position={[0, -0.5, 0]}>
      {!isStructuralLayout && (
        <group>
          {Array.from({length: vRods}).map((_, i) => (
             <Box key={`lv_${i}`} args={[0.06, 1, 0.06]} position={[(i - total/2) * 0.4, 0.5, 0.5]}><meshStandardMaterial color="#ef4444" /></Box>
          ))}
          {Array.from({length: hRods}).map((_, i) => (
             <Box key={`lh_${i}`} args={[1, 0.06, 0.06]} position={[(i - total/2) * 0.4, 0.1, 0]}><meshStandardMaterial color="#ef4444" /></Box>
          ))}
          {Array.from({length: connectors}).map((_, i) => (
             <mesh key={`lc_${i}`} position={[(i - total/2) * 0.4, 0.1, -0.5]}><sphereGeometry args={[0.08]} /><meshStandardMaterial color="#ef4444" /></mesh>
          ))}
          {Array.from({length: panels}).map((_, i) => (
             <Box key={`lp_${i}`} args={[0.6, 0.04, 0.6]} position={[(i - total/2) * 0.4, 0.5, -0.8]} rotation={[Math.PI/4, 0, 0]}><meshStandardMaterial color="#ef4444" /></Box>
          ))}
        </group>
      )}

      {isStructuralLayout && (
        <group position={[0, 0, 0]}>
          {Array.from({length: Math.min(4, vRods)}).map((_, i) => (
             <Box key={`v_${i}`} args={[0.06, 1, 0.06]} position={[positions[i % 4][0], 0.5, positions[i % 4][1]]}><meshStandardMaterial color="#334155" /></Box>
          ))}
          {Array.from({length: Math.min(4, connectors)}).map((_, i) => (
             <mesh key={`c_${i}`} position={[positions[i % 4][0], 1.0, positions[i % 4][1]]}><sphereGeometry args={[0.08]} /><meshStandardMaterial color="#0f172a" /></mesh>
          ))}
          {hRods >= 1 && <Box args={[1, 0.06, 0.06]} position={[0, 1.0, 0.5]}><meshStandardMaterial color="#334155" /></Box>}
          {hRods >= 2 && <Box args={[1, 0.06, 0.06]} position={[0, 1.0, -0.5]}><meshStandardMaterial color="#334155" /></Box>}
          {hRods >= 3 && <Box args={[0.06, 0.06, 1]} position={[0.5, 1.0, 0]}><meshStandardMaterial color="#334155" /></Box>}
          {hRods >= 4 && <Box args={[0.06, 0.06, 1]} position={[-0.5, 1.0, 0]}><meshStandardMaterial color="#334155" /></Box>}
          {panels >= 1 && <Box args={[1, 0.04, 1]} position={[0, 1.05, 0]}><meshStandardMaterial color="#f8fafc" metalness={0.1} /><Edges color="#cbd5e1" /></Box>}
        </group>
      )}
    </group>
  );
};

const App = () => {
  const allItems = useMemo(() => generateAllCombos(), []);
  const [selectedLayout, setSelectedLayout] = useState<LayoutItem>(allItems[allItems.length - 1]);
  const [filter, setFilter] = useState<'all' | 'module' | 'grid'>('all');

  const filteredItems = useMemo(() => {
    if (filter === 'module') return allItems.filter(i => i.mode === 'module');
    if (filter === 'grid') return allItems.filter(i => i.mode === 'grid');
    return allItems;
  }, [allItems, filter]);

  return (
    <div style={{ display: 'flex', height: '100vh', overflow: 'hidden' }}>
      <div style={{ width: '450px', display: 'flex', flexDirection: 'column', background: '#fff', boxShadow: '2px 0 12px rgba(0,0,0,0.05)', zIndex: 10 }}>
        <div style={{ padding: '24px', background: 'linear-gradient(135deg, #4f46e5 0%, #3b82f6 100%)', color: 'white' }}>
          <h2 style={{ margin: 0, display: 'flex', alignItems: 'center', fontSize: '20px', fontWeight: 600 }}>
            <LayoutDashboard style={{ marginRight: '10px' }} size={24} />
            全新规则 R6 注入验证
          </h2>
          <p style={{ margin: '8px 0 0 0', opacity: 0.9, fontSize: '13px', lineHeight: 1.5 }}>
            核心：验证“提升单位占地下的存取效率”<br/>
            排布必须突破单层(L1)，发生 L2 层以上拓展
          </p>
        </div>

        <div style={{ padding: '16px 20px 10px 20px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid #e2e8f0', paddingBottom:'16px' }}>
          <h3 style={{ margin: 0, fontSize: '15px', color: '#475569', display: 'flex', alignItems: 'center' }}>
            <Grid size={16} style={{ marginRight: '6px' }} /> 场景视图筛选
          </h3>
          <div style={{ display: 'flex', gap: '6px' }}>
            {/* <button onClick={() => setFilter('all')} style={{ padding:'4px 10px', fontSize:'12px', cursor:'pointer', border:'none', borderRadius:'12px', background: filter==='all'?'#e0e7ff':'#f1f5f9', color: filter==='all'?'#4f46e5':'#64748b' }}>全部</button> */}
            <button onClick={() => setFilter('module')} style={{ padding:'4px 10px', fontSize:'12px', cursor:'pointer', border:'none', borderRadius:'12px', background: filter==='module'?'#e0e7ff':'#f1f5f9', color: filter==='module'?'#4f46e5':'#64748b' }}>底层单元测试</button>
            <button onClick={() => setFilter('grid')} style={{ padding:'4px 10px', fontSize:'12px', cursor:'pointer', border:'none', borderRadius:'12px', background: filter==='grid'?'#e0e7ff':'#f1f5f9', color: filter==='grid'?'#4f46e5':'#64748b' }}>多层平移阵列</button>
          </div>
        </div>

        <div style={{ flex: 1, overflowY: 'auto', padding: '10px 20px 20px 20px' }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {filteredItems.map(layout => {
              const isSelected = selectedLayout.id === layout.id;
              return (
                <button
                  key={layout.id}
                  onClick={() => setSelectedLayout(layout)}
                  style={{
                    display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                    padding: '12px', cursor: 'pointer', textAlign: 'left',
                    background: isSelected ? '#4f46e5' : '#ffffff',
                    color: isSelected ? '#ffffff' : '#334155',
                    border: `1px solid ${isSelected ? '#4f46e5' : '#e2e8f0'}`,
                    borderRadius: '8px',
                    transition: 'all 0.2s'
                  }}
                >
                  <div style={{ display: 'flex', flexDirection: 'column' }}>
                    <span style={{ fontSize: '13px', color: isSelected ? '#a5b4fc' : '#94a3b8', marginBottom: '4px' }}>[{layout.group}]</span>
                    <span style={{ fontSize: '14px', fontWeight: 600 }}>{layout.name}</span>
                    <span style={{ fontSize: '12px', marginTop: '4px', color: isSelected ? '#e0e7ff' : '#64748b' }}>
                       {layout.vRods}竖 · {layout.hRods}横 · {layout.connectors}接口 · {layout.panels}层板
                    </span>
                  </div>
                  {layout.valid ? 
                     <CheckCircle2 size={20} color={isSelected ? '#a7f3d0' : '#10b981'} /> : 
                     <XCircle size={20} color={isSelected ? '#fecaca' : '#ef4444'} />
                  }
                </button>
              )
            })}
          </div>
        </div>
      </div>

      <div style={{ flex: 1, position: 'relative', background: '#f8fafc' }}>
        <div className="glass-panel" style={{
          position: 'absolute', top: 24, right: 24, zIndex: 10,
          padding: '20px', borderRadius: '16px', minWidth: '380px',
          background: 'rgba(255,255,255,0.8)', backdropFilter: 'blur(12px)',
          boxShadow: '0 4px 20px rgba(0,0,0,0.05)', border: '1px solid #fff'
        }}>
          <h3 style={{ margin: '0 0 16px 0', fontSize: '18px', color: '#1e293b' }}>
            结构效率测算 (R6法则)
          </h3>
          <div style={{ marginBottom: '16px' }}>
            {selectedLayout.valid ?
              <span style={{ background: '#dcfce7', color: '#166534', padding: '4px 10px', borderRadius: '12px', fontSize: '12px', fontWeight: 600, display: 'inline-flex', alignItems: 'center' }}>
                <CheckCircle2 size={14} style={{ marginRight: '4px' }} /> 完全达标
              </span> :
              <span style={{ background: '#fee2e2', color: '#991b1b', padding: '4px 10px', borderRadius: '12px', fontSize: '12px', fontWeight: 600, display: 'inline-flex', alignItems: 'center' }}>
                <XCircle size={14} style={{ marginRight: '4px' }} /> {selectedLayout.mode==='grid'?'高度不达标 (触犯R6效率底线)':'结构畸形或不完整 (基础拦截)'}
              </span>
            }
          </div>
          
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', background: 'rgba(255,255,255,0.5)', padding: '12px', borderRadius: '8px' }}>
             <div style={{ fontSize: '13px', color: '#64748b'}}>竖向支撑杆: <strong style={{color:'#334155'}}>{selectedLayout.vRods} 根</strong></div>
             <div style={{ fontSize: '13px', color: '#64748b'}}>横向连接杆: <strong style={{color:'#334155'}}>{selectedLayout.hRods} 根</strong></div>
             <div style={{ fontSize: '13px', color: '#64748b'}}>四向连接接口: <strong style={{color:'#334155'}}>{selectedLayout.connectors} 个</strong></div>
             <div style={{ fontSize: '13px', color: '#64748b'}}>高密度层板: <strong style={{color:'#334155'}}>{selectedLayout.panels} 块</strong></div>
          </div>
          
          <div style={{ marginTop: '16px', background: selectedLayout.valid ? '#e0e7ff' : '#fef2f2', padding: '12px', borderRadius: '8px', fontSize: '13px', color: '#334155', fontWeight: 500, lineHeight: 1.5 }}>
            {selectedLayout.reason}
          </div>
        </div>

        {selectedLayout.mode === 'grid' && selectedLayout.gridLayers && (
          <div style={{ position: 'absolute', bottom: 24, right: 24, zIndex: 10, background: '#fff', padding: '12px', borderRadius: '8px', boxShadow: '0 4px 12px rgba(0,0,0,0.05)' }}>
             <div style={{ fontSize: '12px', color: '#64748b', marginBottom: '8px', textAlign: 'center' }}>
                2x2地块平面投影 (含层数)
             </div>
             <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '4px' }}>
                {[0, 1, 2, 3].map(idx => (
                   <div key={idx} style={{ 
                      width: '38px', height: '38px', 
                      background: selectedLayout.gridLayers![idx] > 0 ? '#4f46e5' : '#f1f5f9', 
                      borderRadius: '4px', border: '1px solid #e2e8f0',
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                      color: selectedLayout.gridLayers![idx] > 0 ? '#fff' : '#cbd5e1',
                      fontSize: '12px', fontWeight: 'bold'
                   }}>
                      {selectedLayout.gridLayers![idx] > 0 ? `L${selectedLayout.gridLayers![idx]}` : '空'}
                   </div>
                ))}
             </div>
          </div>
        )}

        <Canvas camera={{ position: [6, 5, 8], fov: 45 }}>
          <color attach="background" args={['#e2e8f0']} />
          <ambientLight intensity={0.6} />
          <directionalLight position={[10, 15, 10]} intensity={1.5} castShadow />
          <directionalLight position={[-10, 5, -5]} intensity={0.5} />
          <Environment preset="city" />
          <group position={[0, -0.5, 0]}>
            {selectedLayout.mode === 'grid' && selectedLayout.gridLayers ? 
               <GridModel layers={selectedLayout.gridLayers} /> : 
               <ModuleModel modules={selectedLayout.modules || []} />
            }
            <ContactShadows resolution={1024} scale={10} blur={2.5} opacity={0.5} far={10} color="#334155" />
          </group>
          <OrbitControls makeDefault autoRotate autoRotateSpeed={1.0} enablePan={true} target={[0, 1.5, 0]} />
        </Canvas>
      </div>
    </div>
  );
};

export default App;
