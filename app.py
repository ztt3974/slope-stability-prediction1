# -*- coding: utf-8 -*-
"""
边坡稳定性预测系统 - Streamlit Web应用
基于IPSO-BP优化集成学习模型
"""

import os
import sys
import warnings

os.environ['PYTHONIOENCODING'] = 'utf-8'
warnings.filterwarnings('ignore')

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import io
import contextlib

try:
    from openpyxl import Workbook
except ImportError:
    pass

import sys
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0,current_dir)
from ipso_bp_slope_stability import create_features, OptimizedEnsemble

st.set_page_config(
    page_title="边坡稳定性预测系统",
    page_icon="⛰️",
    layout="wide",
    initial_sidebar_state="expanded"
)

OPTIMAL_THRESHOLD = 0.7160
MODEL_PATH = os.path.join(current_dir, 'ipso_bp_ensemble_model.pkl')

@st.cache_resource
def load_model():
    """加载训练好的集成模型（带缓存）- 彻底解决 Windows GBK 编码问题"""
    if os.path.exists(MODEL_PATH):
        try:
            import joblib
            
            original_stdout = sys.stdout
            original_stderr = sys.stderr
            
            try:
                devnull = open(os.devnull, 'w', encoding='utf-8', errors='replace')
                sys.stdout = devnull
                sys.stderr = devnull
                
                model = joblib.load(MODEL_PATH)
                
            finally:
                sys.stdout = original_stdout
                sys.stderr = original_stderr
                if 'devnull' in locals():
                    devnull.close()
            
            return model, True, "模型加载成功"
            
        except UnicodeEncodeError as e:
            return None, False, f"⚠️ 模型编码错误: {str(e)}<br><br>**解决方案**:<br>1. 运行修复脚本: `python fix_encoding.py`<br>2. 使用修复后的脚本重新训练: `python ipso_bp_slope_stability_fixed.py`<br>3. 重启本应用"
            
        except Exception as e:
            error_msg = str(e)
            if 'codec' in error_msg.lower() or 'encode' in error_msg.lower():
                return None, False, f"⚠️ 模型编码错误: Windows系统无法处理模型中的特殊字符<br><br>**解决方案**:<br>1. 运行: `python ipso_bp_slope_stability_fixed.py` 重新训练<br>2. 将生成的 .pkl 文件复制到 ipso_bp_model_output/ 目录<br>3. 刷新页面"
            else:
                return None, False, f"❌ 模型加载失败: {error_msg}"
    else:
        return None, False, f"📂 模型文件不存在: `{MODEL_PATH}`<br><br>请先运行训练脚本生成模型文件"

def init_session_state():
    """初始化session_state"""
    if 'history' not in st.session_state:
        st.session_state.history = []
    if 'prediction_made' not in st.session_state:
        st.session_state.prediction_made = False

def validate_inputs(H, beta, C, phi, Y, r_u):
    """验证输入参数的合理性"""
    errors = []
    
    if not (0.5 <= H <= 200):
        errors.append(f"坡高 H 应在 0.5-200m 范围内，当前值: {H}")
    if not (5 <= beta <= 90):
        errors.append(f"坡角 β 应在 5-90° 范围内，当前值: {beta}")
    if not (0 <= C <= 500):
        errors.append(f"粘聚力 C 应在 0-500kPa 范围内，当前值: {C}")
    if not (0 <= phi <= 60):
        errors.append(f"内摩擦角 φ 应在 0-60° 范围内，当前值: {phi}")
    if not (10 <= Y <= 30):
        errors.append(f"容重 γ 应在 10-30 kg/m³ 范围内，当前值: {Y}")
    if not (0 <= r_u <= 1):
        errors.append(f"孔隙水压力比 ru 应在 0-1 范围内，当前值: {r_u}")
    
    return errors

def main():
    init_session_state()
    
    st.title("⛰️ 边坡稳定性智能预测系统")
    st.markdown("""
    **基于IPSO-BP优化的集成学习模型**  
    输入边坡几何与力学参数，预测边坡稳定状态
    """)
    
    model, model_loaded, model_msg = load_model()
    
    with st.sidebar:
        st.header("📊 参数输入")
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        
        with col1:
            H = st.number_input(
                "坡高 H (m)",
                min_value=0.5,
                max_value=200.0,
                value=20.0,
                step=1.0,
                help="边坡的高度，单位：米"
            )
            
            beta = st.number_input(
                "坡角 β (°)",
                min_value=5.0,
                max_value=90.0,
                value=45.0,
                step=1.0,
                help="边坡的倾斜角度，单位：度"
            )
            
            C = st.number_input(
                "粘聚力 C (kPa)",
                min_value=0.0,
                max_value=500.0,
                value=25.0,
                step=1.0,
                help="土壤粘聚力，单位：千帕"
            )
        
        with col2:
            phi = st.number_input(
                "内摩擦角 φ (°)",
                min_value=0.0,
                max_value=60.0,
                value=30.0,
                step=1.0,
                help="土壤内摩擦角，单位：度"
            )
            
            Y = st.number_input(
                "容重 γ (kg/m³)",
                min_value=10.0,
                max_value=30.0,
                value=20.0,
                step=0.5,
                help="土壤容重，单位：千克/立方米"
            )
            
            r_u = st.number_input(
                "孔隙水压力比 ru",
                min_value=0.0,
                max_value=1.0,
                value=0.25,
                step=0.05,
                help="孔隙水压力系数，范围0-1"
            )
        
        st.markdown("---")
        
        predict_btn = st.button("🚀 开始预测", type="primary", use_container_width=True)
        
        st.markdown("---")
        st.markdown("**参数说明**")
        st.info("""
        - **H**: 边坡高度 (m)
        - **β**: 坡角角度 (°)  
        - **C**: 土壤粘聚力 (kPa)
        - **φ**: 内摩擦角 (°)
        - **γ**: 土壤容重 (kg/m³)
        - **ru**: 孔隙水压力比
        """)
    
    if not model_loaded:
        st.error(f"⚠️ {model_msg}", icon="🚫")
        st.warning("请确保模型文件已正确放置，或先运行训练脚本生成模型。")
        st.stop()
    
    if predict_btn:
        errors = validate_inputs(H, beta, C, phi, Y, r_u)
        
        if errors:
            st.error("❌ **输入参数验证失败**", icon="🚫")
            for error in errors:
                st.write(f"- {error}")
        else:
            perform_prediction(model, H, beta, C, phi, Y, r_u)
    
    display_results_section()
    display_history_section()

def perform_prediction(model, H, beta, C, phi, Y, r_u):
    """执行预测流程"""
    try:
        input_data = pd.DataFrame([{
            '容重 Y(kg/m3)': Y,
            '粘聚力 C(kPa)': C,
            '内摩擦角 φ(°)': phi,
            '坡角 β(°)': beta,
            '坡高 H(m)': H,
            '孔隙水压力比 r.': r_u
        }])
        
        with st.spinner("正在进行特征工程和模型推理..."):
            features_enhanced = create_features(input_data)
            
            stability_proba = model.predict_proba(features_enhanced)[0]
            
            prediction = int(stability_proba >= OPTIMAL_THRESHOLD)
            
            status_text = "稳定 ✅" if prediction == 1 else "不稳定 ❌"
            
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            record = {
                '时间戳': timestamp,
                '坡高 H(m)': H,
                '坡角 β(°)': beta,
                '粘聚力 C(kPa)': C,
                '内摩擦角 φ(°)': phi,
                '容重 γ (kg/m³)': Y,
                '孔隙水压力比 ru': r_u,
                '预测状态': status_text,
                '稳定概率': round(stability_proba * 100, 2),
                '使用阈值': OPTIMAL_THRESHOLD
            }
            
            st.session_state.history.insert(0, record)
            st.session_state.prediction_result = {
                'prediction': prediction,
                'probability': stability_proba,
                'status': status_text,
                'input_params': {
                    'H': H, 'beta': beta, 'C': C,
                    'phi': phi, 'Y': Y, 'r_u': r_u
                }
            }
            st.session_state.prediction_made = True
            
            st.success("✅ 预测完成！", icon="✅")
            st.balloons()
            
    except Exception as e:
        st.error(f"❌ 预测过程出错: {str(e)}", icon="🚫")
        st.error("请检查输入参数或联系系统管理员")

def display_results_section():
    """显示预测结果区域"""
    if st.session_state.prediction_made and hasattr(st.session_state, 'prediction_result'):
        result = st.session_state.prediction_result
        
        st.markdown("---")
        st.header("📈 预测结果")
        
        col_result, col_prob = st.columns([1, 2])
        
        with col_result:
            if result['prediction'] == 1:
                st.markdown("""
                <div style="
                    background: linear-gradient(135deg, #00c853, #69f0ae);
                    padding: 30px;
                    border-radius: 15px;
                    text-align: center;
                    color: white;
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                ">
                    <h2 style="margin: 0; font-size: 48px;">✅</h2>
                    <h3 style="margin: 10px 0 0 0;">稳 定</h3>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div style="
                    background: linear-gradient(135deg, #ff5252, #ff8a80);
                    padding: 30px;
                    border-radius: 15px;
                    text-align: center;
                    color: white;
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                ">
                    <h2 style="margin: 0; font-size: 48px;">❌</h2>
                    <h3 style="margin: 10px 0 0 0;">不稳定</h3>
                </div>
                """, unsafe_allow_html=True)
        
        with col_prob:
            st.subheader("稳定概率")
            prob_percent = result['probability'] * 100
            
            prob_color = "#00c853" if result['prediction'] == 1 else "#ff5252"
            
            st.markdown(f"""
            <div style="
                background: #f5f5f5;
                border-radius: 10px;
                padding: 20px;
                margin-top: 10px;
            ">
                <div style="
                    font-size: 36px;
                    font-weight: bold;
                    color: {prob_color};
                    text-align: center;
                    margin-bottom: 15px;
                ">
                    {prob_percent:.2f}%
                </div>
                <div style="
                    background: #e0e0e0;
                    border-radius: 8px;
                    height: 25px;
                    overflow: hidden;
                ">
                    <div style="
                        background: linear-gradient(90deg, {prob_color}, {'#69f0ae' if result['prediction'] == 1 else '#ff8a80'});
                        height: 100%;
                        width: {min(prob_percent, 100)}%;
                        transition: width 0.5s ease;
                        border-radius: 8px;
                    "></div>
                </div>
                <div style="
                    text-align: center;
                    margin-top: 10px;
                    color: #666;
                    font-size: 14px;
                ">
                    判断阈值: {OPTIMAL_THRESHOLD} ({OPTIMAL_THRESHOLD*100:.2f}%)
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        with st.expander("📋 查看输入参数详情", expanded=False):
            params_df = pd.DataFrame([
                {"参数": "坡高 H", "值": f"{result['input_params']['H']} m"},
                {"参数": "坡角 β", "值": f"{result['input_params']['beta']}°"},
                {"参数": "粘聚力 C", "值": f"{result['input_params']['C']} kPa"},
                {"参数": "内摩擦角 φ", "值": f"{result['input_params']['phi']}°"},
                {"参数": "容重 γ", "值": f"{result['input_params']['Y']} kg/m³"},
                {"参数": "孔隙水压力比 ru", "值": result['input_params']['r_u']}
            ])
            st.table(params_df)

def display_history_section():
    """显示历史记录区域"""
    st.markdown("---")
    st.header("📜 预测历史记录")
    
    if len(st.session_state.history) == 0:
        st.info("暂无预测记录，请在左侧输入参数并进行预测")
        return
    
    col_table, col_export = st.columns([3, 1])
    
    with col_export:
        export_format = st.selectbox(
            "导出格式",
            ["Excel (.xlsx)", "CSV (.csv)"],
            label_visibility="collapsed"
        )
        
        if st.button("📥 导出记录", use_container_width=True):
            export_history(export_format)
        
        if st.button("🗑️ 清空记录", use_container_width=True):
            st.session_state.history = []
            st.success("历史记录已清空")
            st.rerun()
    
    with col_table:
        history_df = pd.DataFrame(st.session_state.history)
        
        st.dataframe(
            history_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "时间戳": st.column_config.TextColumn("时间戳", width="medium"),
                "预测状态": st.column_config.TextColumn("状态", width="small"),
                "稳定概率": st.column_config.ProgressColumn(
                    "稳定概率 (%)",
                    format="%f%%",
                    min_value=0,
                    max_value=100
                ),
                "坡高 H(m)": st.column_config.NumberColumn("H (m)", format="%.1f"),
                "坡角 β(°)": st.column_config.NumberColumn("β (°)", format="%.1f"),
                "粘聚力 C(kPa)": st.column_config.NumberColumn("C (kPa)", format="%.1f"),
                "内摩擦角 φ(°)": st.column_config.NumberColumn("φ (°)", format="%.1f"),
                "容重 γ (kg/m³)": st.column_config.NumberColumn("γ (kg/m³)", format="%.1f"),
                "孔隙水压力比 ru": st.column_config.NumberColumn("ru", format="%.3f"),
                "使用阈值": st.column_config.NumberColumn("阈值", format="%.4f")
            }
        )
        
        st.info(f"共 {len(st.session_state.history)} 条预测记录")

def export_history(format_type):
    """导出历史记录"""
    if len(st.session_state.history) == 0:
        st.warning("没有可导出的记录")
        return
    
    try:
        history_df = pd.DataFrame(st.session_state.history)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if "Excel" in format_type:
            filename = f"slope_stability_history_{timestamp}.xlsx"
            history_df.to_excel(filename, index=False, engine='openpyxl')
            st.success(f"✅ 已导出为 Excel 文件: {filename}")
        else:
            filename = f"slope_stability_history_{timestamp}.csv"
            history_df.to_csv(filename, index=False, encoding='utf-8-sig')
            st.success(f"✅ 已导出为 CSV 文件: {filename}")
        
        with open(filename, 'rb') as f:
            st.download_button(
                label="📥 下载文件",
                data=f,
                file_name=filename,
                mime="application/vnd.ms-excel" if "Excel" in format_type else "text/csv"
            )
            
    except Exception as e:
        st.error(f"导出失败: {str(e)}")

if __name__ == "__main__":
    main()
