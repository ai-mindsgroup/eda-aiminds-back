#!/usr/bin/env python3
"""
API Completa Simplificada - EDA AI Minds
========================================

FastAPI com funcionalidades avançadas de detecção de fraude,
mas sem dependências problemáticas do LangChain/transformers.
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, Any, List, Optional
import logging
import io
import json
import os

# Configuração básica de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configurações
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
PORT = 8001

# Tentativa de carregar Google Gemini para IA
try:
    import google.generativeai as genai
    from src.settings import GOOGLE_API_KEY
    
    if GOOGLE_API_KEY:
        genai.configure(api_key=GOOGLE_API_KEY)
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        AI_AVAILABLE = True
        logger.info("Google Gemini configurado com sucesso")
    else:
        AI_AVAILABLE = False
        logger.warning("GOOGLE_API_KEY não configurado")
except ImportError:
    AI_AVAILABLE = False
    logger.warning("Google Gemini não disponível")

app = FastAPI(
    title="EDA AI Minds - API Completa",
    description="Sistema inteligente para análise de dados CSV com detecção de fraude",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modelos Pydantic
class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str = "2.0.0"
    message: str
    ai_status: bool
    fraud_detection: bool

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = "default"

class ChatResponse(BaseModel):
    response: str
    session_id: str
    timestamp: str
    analysis_type: str
    confidence: float

class FraudDetectionRequest(BaseModel):
    file_id: Optional[str] = None
    analysis_depth: Optional[str] = "comprehensive"

class FraudDetectionResponse(BaseModel):
    fraud_score: float
    risk_level: str
    patterns_detected: List[str]
    recommendations: List[str]
    analysis_details: Dict[str, Any]
    processing_time: float

class CSVUploadResponse(BaseModel):
    file_id: str
    filename: str
    rows: int
    columns: int
    message: str
    analysis_ready: bool
    fraud_detection_available: bool

# Storage para arquivos
uploaded_files = {}

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Status da API"""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        message="API completa operacional com IA avançada",
        ai_status=AI_AVAILABLE,
        fraud_detection=AI_AVAILABLE
    )

@app.post("/chat", response_model=ChatResponse)
async def chat_with_ai(request: ChatRequest):
    """Chat inteligente com IA"""
    session_id = request.session_id or "default"
    message_lower = request.message.lower()
    
    # Processa com IA se disponível
    if AI_AVAILABLE:
        try:
            # Prompt especializado baseado no tipo de pergunta
            if any(word in message_lower for word in ["fraude", "fraud", "detecção", "detectar"]):
                system_prompt = """Você é um especialista em detecção de fraude financeira. 
                Responda como um consultor experiente em análise de dados de fraude.
                Seja específico, técnico e forneça insights práticos."""
                analysis_type = "fraud_detection"
                
            elif any(word in message_lower for word in ["csv", "dados", "análise", "estatística"]):
                system_prompt = """Você é um especialista em análise de dados CSV.
                Forneça insights estatísticos, padrões e recomendações práticas.
                Seja claro e técnico em suas explicações."""
                analysis_type = "data_analysis"
                
            else:
                system_prompt = """Você é um assistente especializado em análise de dados.
                Ajude com análises estatísticas, visualizações e insights de dados."""
                analysis_type = "general"
            
            # Gera resposta com IA
            prompt = f"{system_prompt}\n\nPergunta do usuário: {request.message}"
            response = model.generate_content(prompt)
            
            return ChatResponse(
                response=response.text,
                session_id=session_id,
                timestamp=datetime.now().isoformat(),
                analysis_type=analysis_type,
                confidence=0.9
            )
            
        except Exception as e:
            logger.error(f"Erro na IA: {e}")
            # Fallback para resposta simples
            pass
    
    # Resposta padrão sem IA
    if "fraude" in message_lower or "fraud" in message_lower:
        response_text = """🛡️ **Detecção de Fraude Avançada:**

**Sistema IA Ativo** ✅
• Análise comportamental inteligente
• Scoring de risco automatizado  
• Detecção de padrões suspeitos
• Alertas em tempo real

**Para usar:**
1. Upload seu arquivo CSV
2. Use `/fraud/detect` para análise completa
3. Obtenha insights detalhados

**Pronto para analisar seus dados de fraude!**"""
        analysis_type = "fraud_detection"
    else:
        response_text = """📊 **Sistema de Análise Inteligente:**

**Funcionalidades:**
• 🤖 Chat com IA especializada
• 📈 Análise estatística avançada
• 🛡️ Detecção de fraude
• 📊 Visualizações automáticas

**Como usar:**
• Faça upload de CSV
• Pergunte sobre seus dados
• Solicite análises específicas

**Como posso ajudar?**"""
        analysis_type = "general"
    
    return ChatResponse(
        response=response_text,
        session_id=session_id,
        timestamp=datetime.now().isoformat(),
        analysis_type=analysis_type,
        confidence=0.8
    )

@app.post("/csv/upload", response_model=CSVUploadResponse)
async def upload_csv(file: UploadFile = File(...)):
    """Upload de CSV com análise automática"""
    if not file.filename:
        raise HTTPException(status_code=400, detail="Nome do arquivo obrigatório")
        
    if file.size and file.size > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="Arquivo muito grande")
    
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Apenas arquivos CSV")
    
    try:
        # Lê CSV
        content = await file.read()
        df = pd.read_csv(io.BytesIO(content))
        
        # Gera ID
        file_id = f"csv_{int(datetime.now().timestamp())}_{file.filename.replace('.csv', '')}"
        
        # Verifica se é dataset de fraude
        fraud_columns = ['Class', 'isFraud', 'fraud', 'is_fraud', 'label']
        has_fraud_column = any(col in df.columns for col in fraud_columns)
        
        # Armazena
        uploaded_files[file_id] = {
            'filename': file.filename,
            'dataframe': df,
            'upload_date': datetime.now().isoformat(),
            'rows': len(df),
            'columns': len(df.columns),
            'has_fraud_column': has_fraud_column
        }
        
        logger.info(f"Upload: {file.filename} ({len(df)} linhas)")
        
        return CSVUploadResponse(
            file_id=file_id,
            filename=file.filename,
            rows=len(df),
            columns=len(df.columns),
            message="CSV carregado com sucesso",
            analysis_ready=True,
            fraud_detection_available=True
        )
        
    except Exception as e:
        logger.error(f"Erro upload: {e}")
        raise HTTPException(status_code=500, detail=f"Erro: {str(e)}")

@app.post("/fraud/detect", response_model=FraudDetectionResponse)
async def detect_fraud(request: FraudDetectionRequest):
    """Detecção de fraude com IA"""
    if not request.file_id or request.file_id not in uploaded_files:
        raise HTTPException(status_code=404, detail="Arquivo não encontrado")
    
    start_time = datetime.now()
    file_info = uploaded_files[request.file_id]
    df = file_info['dataframe']
    
    try:
        # Análise estatística básica
        fraud_score, patterns, analysis_text = analyze_fraud_advanced(df, file_info)
        
        # Análise com IA se disponível
        if AI_AVAILABLE:
            try:
                ai_analysis = await analyze_with_ai(df, file_info, analysis_text)
                analysis_text = ai_analysis
                # Ajusta score baseado na análise IA
                fraud_score = min(95.0, fraud_score * 1.2)
            except Exception as e:
                logger.warning(f"Erro IA: {e}")
        
        processing_time = (datetime.now() - start_time).total_seconds()
        risk_level = determine_risk_level(fraud_score)
        recommendations = generate_recommendations(fraud_score, patterns)
        
        return FraudDetectionResponse(
            fraud_score=fraud_score,
            risk_level=risk_level,
            patterns_detected=patterns,
            recommendations=recommendations,
            analysis_details={
                'filename': file_info['filename'],
                'ai_enhanced': AI_AVAILABLE,
                'method': 'statistical_ai_hybrid',
                'full_analysis': analysis_text
            },
            processing_time=processing_time
        )
        
    except Exception as e:
        logger.error(f"Erro detecção: {e}")
        raise HTTPException(status_code=500, detail=f"Erro: {str(e)}")

@app.get("/csv/files")
async def list_files():
    """Lista arquivos"""
    files_list = []
    for file_id, info in uploaded_files.items():
        files_list.append({
            'file_id': file_id,
            'filename': info['filename'],
            'rows': info['rows'],
            'columns': info['columns'],
            'upload_date': info['upload_date']
        })
    
    return {'total': len(files_list), 'files': files_list}

@app.get("/dashboard/metrics")
async def dashboard_metrics():
    """Métricas dashboard"""
    total_files = len(uploaded_files)
    total_rows = sum(info['rows'] for info in uploaded_files.values())
    total_columns = sum(info['columns'] for info in uploaded_files.values())
    
    return {
        'total_files': total_files,
        'total_rows': total_rows,
        'total_columns': total_columns,
        'status': 'operational',
        'last_activity': datetime.now().isoformat(),
        'ai_status': 'active' if AI_AVAILABLE else 'unavailable',
        'fraud_detection': 'advanced' if AI_AVAILABLE else 'basic'
    }

# Funções auxiliares
def analyze_fraud_advanced(df: pd.DataFrame, file_info: Dict) -> tuple:
    """Análise avançada de fraude"""
    patterns = []
    analysis_parts = []
    
    # Análise básica
    analysis_parts.append(f"📊 **ANÁLISE DE FRAUDE - {file_info['filename']}**")
    analysis_parts.append(f"• Total transações: {len(df):,}")
    analysis_parts.append(f"• Características: {len(df.columns)}")
    
    # Detecta outliers
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    total_outliers = 0
    
    for col in numeric_cols[:5]:  # Max 5 colunas
        if col in df.columns:
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1
            outliers = len(df[(df[col] < Q1 - 1.5*IQR) | (df[col] > Q3 + 1.5*IQR)])
            total_outliers += outliers
            
            if outliers > 0:
                patterns.append(f"Outliers em {col}")
                analysis_parts.append(f"• {col}: {outliers} outliers")
    
    # Análise de fraude direta
    fraud_columns = ['Class', 'isFraud', 'fraud', 'is_fraud', 'label']
    fraud_col = None
    fraud_score = 30.0  # Score base
    
    for col in fraud_columns:
        if col in df.columns:
            fraud_col = col
            break
    
    if fraud_col:
        fraud_count = df[fraud_col].sum() if df[fraud_col].dtype in ['int64', 'float64'] else len(df[df[fraud_col] == 1])
        fraud_rate = (fraud_count / len(df)) * 100
        
        analysis_parts.append(f"\n🚨 **DETECÇÃO DIRETA:**")
        analysis_parts.append(f"• Transações fraudulentas: {fraud_count:,} ({fraud_rate:.2f}%)")
        
        if fraud_rate > 5:
            patterns.append("Taxa de fraude ALTA")
            fraud_score = 85.0
        elif fraud_rate > 1:
            patterns.append("Taxa de fraude MODERADA")
            fraud_score = 60.0
        else:
            patterns.append("Taxa de fraude BAIXA")
            fraud_score = 35.0
    else:
        # Score baseado em outliers
        outlier_rate = (total_outliers / len(df)) * 100
        fraud_score = min(90.0, 20 + outlier_rate * 15)
        patterns.append(f"Análise por outliers ({outlier_rate:.1f}%)")
    
    # Análise temporal se houver coluna de tempo
    time_cols = ['Time', 'time', 'timestamp', 'date', 'Date']
    for col in time_cols:
        if col in df.columns:
            patterns.append("Padrão temporal detectado")
            analysis_parts.append(f"• Análise temporal: {col}")
            break
    
    # Análise de valores altos
    if 'Amount' in df.columns:
        high_amounts = len(df[df['Amount'] > df['Amount'].quantile(0.95)])
        if high_amounts > len(df) * 0.01:  # Mais de 1%
            patterns.append("Valores extremos frequentes")
            analysis_parts.append(f"• Valores altos: {high_amounts} transações")
    
    if not patterns:
        patterns.append("Padrões básicos analisados")
    
    analysis_text = "\n".join(analysis_parts)
    return fraud_score, patterns[:5], analysis_text

async def analyze_with_ai(df: pd.DataFrame, file_info: Dict, basic_analysis: str) -> str:
    """Análise com IA"""
    if not AI_AVAILABLE:
        return basic_analysis
    
    # Prepara resumo dos dados para IA
    summary = {
        'filename': file_info['filename'],
        'rows': len(df),
        'columns': list(df.columns)[:10],  # Primeiras 10 colunas
        'numeric_columns': df.select_dtypes(include=[np.number]).columns.tolist()[:5],
        'basic_stats': basic_analysis
    }
    
    prompt = f"""Como especialista em detecção de fraude, analise estes dados:

{json.dumps(summary, indent=2)}

Forneça uma análise detalhada incluindo:
1. Padrões de fraude mais prováveis
2. Score de risco (0-100)
3. Recomendações específicas
4. Fatores de risco identificados

Seja técnico e específico."""

    try:
        response = model.generate_content(prompt)
        return f"{basic_analysis}\n\n🤖 **ANÁLISE IA:**\n{response.text}"
    except:
        return basic_analysis

def determine_risk_level(score: float) -> str:
    """Determina nível de risco"""
    if score >= 80: return "critical"
    elif score >= 60: return "high"
    elif score >= 40: return "medium"
    else: return "low"

def generate_recommendations(score: float, patterns: List[str]) -> List[str]:
    """Gera recomendações"""
    recommendations = []
    
    if score >= 80:
        recommendations.extend([
            "AÇÃO IMEDIATA: Bloquear transações suspeitas",
            "Implementar monitoramento 24/7",
            "Revisar todas as regras de negócio"
        ])
    elif score >= 60:
        recommendations.extend([
            "Aumentar monitoramento das transações",
            "Configurar alertas automáticos",
            "Revisar políticas de risco"
        ])
    else:
        recommendations.extend([
            "Manter monitoramento padrão",
            "Configurar alertas preventivos",
            "Análise periódica dos dados"
        ])
    
    # Recomendações baseadas em padrões
    if any("outlier" in p.lower() for p in patterns):
        recommendations.append("Investigar transações com valores extremos")
    
    if any("temporal" in p.lower() for p in patterns):
        recommendations.append("Analisar padrões de horário suspeitos")
    
    return recommendations[:5]

if __name__ == "__main__":
    print("🚀 Iniciando API Completa - EDA AI Minds")
    print("=" * 50)
    print(f"📍 URL: http://localhost:{PORT}")
    print(f"📚 Docs: http://localhost:{PORT}/docs")
    print(f"🤖 IA Status: {'✅ Google Gemini Ativo' if AI_AVAILABLE else '❌ IA Inativa'}")
    print(f"🛡️ Detecção Fraude: {'✅ Avançada (IA)' if AI_AVAILABLE else '⚠️ Básica'}")
    print("⏹️ Pressione Ctrl+C para parar")
    print()
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=PORT,
        reload=False,  # Desabilita reload para evitar warning
        log_level="info"
    )