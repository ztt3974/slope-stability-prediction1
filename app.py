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
    page_title="Slope Stability Prediction System",
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
            
            return model, True, "Model loaded successfully"
            
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
    """Validate input parameters"""
    errors = []
    
    if not (0.5 <= H <= 500):
        errors.append(f"Slope Height H should be in range 0.5-500m，current value: {H}")
    if not (5 <= beta <= 90):
        errors.append(f"Slope Angle β should be in range 5-90°，current value: {beta}")
    if not (0 <= C <= 500):
        errors.append(f"Cohesion C should be in range 0-500kPa，current value: {C}")
    if not (0 <= phi <= 60):
        errors.append(f"Internal Friction Angle φ should be in range 0-60°，current value: {phi}")
    if not (5 <= Y <= 50):
        errors.append(f"Unit Weight γ should be in range 5-50 kg/m³，current value: {Y}")
    if not (0 <= r_u <= 1):
        errors.append(f"Pore Water Pressure Ratio ru should be in range 0-1，current value: {r_u}")
    
    return errors

def main():
    init_session_state()
    
    st.title("⛰️ Slope Stability Intelligent Prediction System")
    st.markdown("""
    **Based on Ensemble Learning Model**  
    Input slope geometry and mechanical parameters to predict slope stability
    """)
    
    model, model_loaded, model_msg = load_model()
    
    with st.sidebar:
        st.header("📊 Parameter Input")
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        
        with col1:
            H = st.number_input(
                "Slope Height H (m)",
                min_value=0.5,
                max_value=500.0,
                value=20.0,
                step=1.0,
                help="Height of the slope, unit: meters"
            )
            
            beta = st.number_input(
                "Slope Angle β (°)",
                min_value=5.0,
                max_value=90.0,
                value=45.0,
                step=1.0,
                help="Inclination angle of the slope, unit: degrees"
            )
            
            C = st.number_input(
                "Cohesion C (kPa)",
                min_value=0.0,
                max_value=500.0,
                value=25.0,
                step=1.0,
                help="Soil cohesion, unit: kilopascals"
            )
        
        with col2:
            phi = st.number_input(
                "Internal Friction Angle φ (°)",
                min_value=0.0,
                max_value=60.0,
                value=30.0,
                step=1.0,
                help="Soil internal friction angle, unit: degrees"
            )
            
            Y = st.number_input(
                "Unit Weight γ (kg/m³)",
                min_value=5.0,
                max_value=50.0,
                value=20.0,
                step=0.5,
                help="Soil unit weight, unit: kilograms per cubic meter"
            )
            
            r_u = st.number_input(
                "Pore Water Pressure Ratio ru",
                min_value=0.0,
                max_value=1.0,
                value=0.25,
                step=0.05,
                help="Pore water pressure coefficient, range: 0-1"
            )
        
        st.markdown("---")
        
        predict_btn = st.button("🚀 Start Prediction", type="primary", use_container_width=True)
        
        st.markdown("---")
        st.markdown("**Parameter Description**")
        st.info("""
        - **H**: Slope Height (m)
        - **β**: Slope Angle (°)  
        - **C**: Soil Cohesion (kPa)
        - **φ**: Internal Friction Angle (°)
        - **γ**: Unit Weight (kg/m³)
        - **ru**: Pore Water Pressure Ratio
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
            
            status_text = "Stable ✅" if prediction == 1 else "Unstable ❌"
            
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            record = {
                'Timestamp': timestamp,
                'Slope Height H(m)': H,
                'Slope Angle β(°)': beta,
                'Cohesion C(kPa)': C,
                'Internal Friction Angle φ(°)': phi,
                'Unit Weight γ (kg/m³)': Y,
                'Pore Water Pressure Ratio ru': r_u,
                'Prediction Status': status_text,
                'Stability Probability': round(stability_proba * 100, 2),
                'Used Threshold': OPTIMAL_THRESHOLD
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
            
            st.success("✅ Prediction Complete！", icon="✅")
            st.balloons()
            
    except Exception as e:
        st.error(f"❌ Prediction Error: {str(e)}", icon="🚫")
        st.error("Please check input parameters or contact system administrator")

def display_results_section():
    """Display prediction results section"""
    if st.session_state.prediction_made and hasattr(st.session_state, 'prediction_result'):
        result = st.session_state.prediction_result
        
        st.markdown("---")
        st.header("📈 Prediction Results")
        
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
                    <h3 style="margin: 10px 0 0 0;">STABLE</h3>
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
                    <h3 style="margin: 10px 0 0 0;">UNSTABLE</h3>
                </div>
                """, unsafe_allow_html=True)
        
        with col_prob:
            st.subheader("Stability Probability")
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
                    Decision Threshold: {OPTIMAL_THRESHOLD} ({OPTIMAL_THRESHOLD*100:.2f}%)
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        with st.expander("📋 View Input Parameter Details", expanded=False):
            params_df = pd.DataFrame([
                {"Parameter": "Slope Height H", "Value": f"{result['input_params']['H']} m"},
                {"Parameter": "Slope Angle β", "Value": f"{result['input_params']['beta']}°"},
                {"Parameter": "Cohesion C", "Value": f"{result['input_params']['C']} kPa"},
                {"Parameter": "Internal Friction Angle φ", "Value": f"{result['input_params']['phi']}°"},
                {"Parameter": "Unit Weight γ", "Value": f"{result['input_params']['Y']} kg/m³"},
                {"Parameter": "Pore Water Pressure Ratio ru", "Value": result['input_params']['r_u']}
            ])
            st.table(params_df)

def display_history_section():
    """Display prediction history section"""
    st.markdown("---")
    st.header("📜 Prediction History")
    
    if len(st.session_state.history) == 0:
        st.info("No prediction records yet. Please input parameters on the left and perform prediction.")
        return
    
    col_table, col_export = st.columns([3, 1])
    
    with col_export:
        export_format = st.selectbox(
            "Export Format",
            ["Excel (.xlsx)", "CSV (.csv)"],
            label_visibility="collapsed"
        )
        
        if st.button("📥 Export Records", use_container_width=True):
            export_history(export_format)
        
        if st.button("🗑️ Clear Records", use_container_width=True):
            st.session_state.history = []
            st.success("History cleared successfully")
            st.rerun()
    
    with col_table:
        history_df = pd.DataFrame(st.session_state.history)
        
        st.dataframe(
            history_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Timestamp": st.column_config.TextColumn("时间戳", width="medium"),
                "Prediction Status": st.column_config.TextColumn("状态", width="small"),
                "Stability Probability": st.column_config.ProgressColumn(
                    "Stability Probability (%)",
                    format="%f%%",
                    min_value=0,
                    max_value=100
                ),
                "Slope Height H(m)": st.column_config.NumberColumn("H (m)", format="%.1f"),
                "Slope Angle β(°)": st.column_config.NumberColumn("β (°)", format="%.1f"),
                "Cohesion C(kPa)": st.column_config.NumberColumn("C (kPa)", format="%.1f"),
                "Internal Friction Angle φ(°)": st.column_config.NumberColumn("φ (°)", format="%.1f"),
                "Unit Weight γ (kg/m³)": st.column_config.NumberColumn("γ (kg/m³)", format="%.1f"),
                "Pore Water Pressure Ratio ru": st.column_config.NumberColumn("ru", format="%.3f"),
                "Used Threshold": st.column_config.NumberColumn("阈值", format="%.4f")
            }
        )
        
        st.info(f"共 {len(st.session_state.history)} 条预测记录")

def export_history(format_type):
    """Export prediction history"""
    if len(st.session_state.history) == 0:
        st.warning("No records to export")
        return
    
    try:
        history_df = pd.DataFrame(st.session_state.history)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if "Excel" in format_type:
            filename = f"slope_stability_history_{timestamp}.xlsx"
            history_df.to_excel(filename, index=False, engine='openpyxl')
            st.success(f"✅ Exported to Excel file: {filename}")
        else:
            filename = f"slope_stability_history_{timestamp}.csv"
            history_df.to_csv(filename, index=False, encoding='utf-8-sig')
            st.success(f"✅ Exported to CSV file: {filename}")
        
        with open(filename, 'rb') as f:
            st.download_button(
                label="📥 Download File",
                data=f,
                file_name=filename,
                mime="application/vnd.ms-excel" if "Excel" in format_type else "text/csv"
            )
            
    except Exception as e:
        st.error(f"Export failed: {str(e)}")

if __name__ == "__main__":
    main()
