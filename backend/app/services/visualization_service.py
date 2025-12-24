"""
可视化反馈服务
生成雷达图、热力图、对比图等可视化图表
"""
import io
import base64
from typing import Dict, List, Optional, Any
import numpy as np

class VisualizationService:
    """可视化服务"""
    
    def __init__(self):
        self.matplotlib_available = False
        self.plotly_available = False
        self._init_libraries()
    
    def _init_libraries(self):
        """初始化绘图库"""
        try:
            import matplotlib
            matplotlib.use('Agg')  # 非交互式后端
            import matplotlib.pyplot as plt
            # 修复numpy 2.0兼容性：设置兼容模式
            import numpy as np
            if hasattr(np, 'str_'):
                # numpy 2.0+
                pass
            self.plt = plt
            self.matplotlib_available = True
        except ImportError:
            print("警告: matplotlib未安装，可视化功能受限")
        except Exception as e:
            print(f"警告: matplotlib初始化失败: {e}")
            self.matplotlib_available = False
        
        try:
            # 延迟加载plotly（避免numpy 2.0兼容性问题）
            # plotly依赖xarray，xarray使用了np.unicode_（numpy 2.0已移除）
            # 只在需要时导入plotly
            self.plotly_available = False  # 延迟加载
            # 检查plotly是否安装，但不立即导入
            import importlib.util
            plotly_spec = importlib.util.find_spec("plotly")
            if plotly_spec is not None:
                self.plotly_available = True
                print("✅ plotly已安装（将延迟加载以避免numpy兼容性问题）")
            else:
                print("警告: plotly未安装，交互式图表功能受限")
        except Exception as e:
            print(f"警告: plotly检查失败: {e}")
            self.plotly_available = False
    
    def generate_radar_chart(
        self,
        categories: List[str],
        values: List[float],
        title: str = "雷达图",
        output_format: str = "png"
    ) -> str:
        """
        生成雷达图（蜘蛛图）
        返回base64编码的图片或文件路径
        """
        if not self.matplotlib_available:
            return ""
        
        try:
            import matplotlib.pyplot as plt
            import numpy as np
            
            # 设置中文字体
            plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
            # numpy 2.0兼容性：使用str_替代unicode_
            if hasattr(np, 'str_'):
                plt.rcParams['axes.unicode_minus'] = False
            else:
                # numpy 1.x兼容
                plt.rcParams['axes.unicode_minus'] = False
            
            # 计算角度
            angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False).tolist()
            values_plot = values + [values[0]]  # 闭合
            angles += angles[:1]
            
            # 创建图形
            fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(projection='polar'))
            
            # 绘制雷达图
            ax.plot(angles, values_plot, 'o-', linewidth=2, label='数值')
            ax.fill(angles, values_plot, alpha=0.25)
            
            # 设置标签
            ax.set_xticks(angles[:-1])
            ax.set_xticklabels(categories)
            ax.set_ylim(0, max(values) * 1.2 if values else 1)
            ax.set_title(title, pad=20)
            ax.grid(True)
            
            # 保存到内存
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format=output_format, bbox_inches='tight', dpi=150)
            plt.close()
            
            # 转换为base64
            img_buffer.seek(0)
            img_base64 = base64.b64encode(img_buffer.read()).decode()
            
            return f"data:image/{output_format};base64,{img_base64}"
        
        except Exception as e:
            print(f"生成雷达图错误: {e}")
            return ""
    
    def generate_heatmap(
        self,
        data_matrix: List[List[float]],
        x_labels: List[str],
        y_labels: List[str],
        title: str = "热力图",
        output_format: str = "png"
    ) -> str:
        """
        生成热力图
        """
        if not self.matplotlib_available:
            return ""
        
        try:
            import matplotlib.pyplot as plt
            import numpy as np
            
            plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
            # numpy 2.0兼容性
            plt.rcParams['axes.unicode_minus'] = False
            
            # 转换为numpy数组
            data = np.array(data_matrix)
            
            # 创建图形
            fig, ax = plt.subplots(figsize=(12, 8))
            
            # 绘制热力图
            im = ax.imshow(data, cmap='YlOrRd', aspect='auto')
            
            # 设置标签
            ax.set_xticks(np.arange(len(x_labels)))
            ax.set_yticks(np.arange(len(y_labels)))
            ax.set_xticklabels(x_labels, rotation=45, ha='right')
            ax.set_yticklabels(y_labels)
            
            # 添加数值标注
            for i in range(len(y_labels)):
                for j in range(len(x_labels)):
                    text = ax.text(j, i, f'{data[i, j]:.2f}',
                                 ha="center", va="center", color="black", fontsize=8)
            
            # 添加颜色条
            plt.colorbar(im, ax=ax)
            ax.set_title(title, pad=20)
            
            # 保存
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format=output_format, bbox_inches='tight', dpi=150)
            plt.close()
            
            img_buffer.seek(0)
            img_base64 = base64.b64encode(img_buffer.read()).decode()
            
            return f"data:image/{output_format};base64,{img_base64}"
        
        except Exception as e:
            print(f"生成热力图错误: {e}")
            return ""
    
    def generate_timeline_chart(
        self,
        time_points: List[str],
        values: List[float],
        title: str = "时间线图表",
        y_label: str = "数值",
        output_format: str = "png"
    ) -> str:
        """
        生成时间线图表
        """
        if not self.matplotlib_available:
            return ""
        
        try:
            import matplotlib.pyplot as plt
            
            plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
            # numpy 2.0兼容性
            plt.rcParams['axes.unicode_minus'] = False
            
            fig, ax = plt.subplots(figsize=(12, 6))
            
            ax.plot(time_points, values, marker='o', linewidth=2, markersize=6)
            ax.fill_between(time_points, values, alpha=0.3)
            
            ax.set_xlabel('时间点', fontsize=12)
            ax.set_ylabel(y_label, fontsize=12)
            ax.set_title(title, fontsize=14, pad=20)
            ax.grid(True, alpha=0.3)
            plt.xticks(rotation=45, ha='right')
            
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format=output_format, bbox_inches='tight', dpi=150)
            plt.close()
            
            img_buffer.seek(0)
            img_base64 = base64.b64encode(img_buffer.read()).decode()
            
            return f"data:image/{output_format};base64,{img_base64}"
        
        except Exception as e:
            print(f"生成时间线图表错误: {e}")
            return ""
    
    def generate_comparison_chart(
        self,
        categories: List[str],
        values_a: List[float],
        values_b: List[float],
        label_a: str = "版本A",
        label_b: str = "版本B",
        title: str = "对比图表",
        chart_type: str = "bar",
        output_format: str = "png"
    ) -> str:
        """
        生成对比图表（柱状图或折线图）
        """
        if not self.matplotlib_available:
            return ""
        
        try:
            import matplotlib.pyplot as plt
            import numpy as np
            
            plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
            # numpy 2.0兼容性
            plt.rcParams['axes.unicode_minus'] = False
            
            fig, ax = plt.subplots(figsize=(12, 6))
            
            x = np.arange(len(categories))
            width = 0.35
            
            if chart_type == "bar":
                ax.bar(x - width/2, values_a, width, label=label_a, alpha=0.8)
                ax.bar(x + width/2, values_b, width, label=label_b, alpha=0.8)
            else:  # line
                ax.plot(x, values_a, marker='o', label=label_a, linewidth=2)
                ax.plot(x, values_b, marker='s', label=label_b, linewidth=2)
            
            ax.set_xlabel('类别', fontsize=12)
            ax.set_ylabel('数值', fontsize=12)
            ax.set_title(title, fontsize=14, pad=20)
            ax.set_xticks(x)
            ax.set_xticklabels(categories, rotation=45, ha='right')
            ax.legend()
            ax.grid(True, alpha=0.3)
            
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format=output_format, bbox_inches='tight', dpi=150)
            plt.close()
            
            img_buffer.seek(0)
            img_base64 = base64.b64encode(img_buffer.read()).decode()
            
            return f"data:image/{output_format};base64,{img_base64}"
        
        except Exception as e:
            print(f"生成对比图表错误: {e}")
            return ""
    
    def generate_text_diff_visualization(
        self,
        text_a: str,
        text_b: str,
        title: str = "文本差异对比"
    ) -> Dict[str, Any]:
        """
        生成文本差异可视化
        使用difflib计算差异
        """
        import difflib
        
        # 计算差异
        diff = list(difflib.unified_diff(
            text_a.splitlines(keepends=True),
            text_b.splitlines(keepends=True),
            lineterm='',
            fromfile='版本A',
            tofile='版本B'
        ))
        
        # 标记差异
        added_lines = []
        removed_lines = []
        unchanged_lines = []
        
        for line in diff:
            if line.startswith('+') and not line.startswith('+++'):
                added_lines.append(line[1:])
            elif line.startswith('-') and not line.startswith('---'):
                removed_lines.append(line[1:])
            elif not line.startswith('@') and not line.startswith('+++') and not line.startswith('---'):
                unchanged_lines.append(line)
        
        return {
            "diff": diff,
            "added": added_lines,
            "removed": removed_lines,
            "unchanged": unchanged_lines,
            "added_count": len(added_lines),
            "removed_count": len(removed_lines)
        }

# 单例模式
visualization_service = VisualizationService()

