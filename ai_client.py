import os
import json
from typing import Dict, Any, Optional
import httpx
from config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL

# Проверяем наличие API ключа
HAS_API_KEY = DEEPSEEK_API_KEY and DEEPSEEK_API_KEY != "" and not DEEPSEEK_API_KEY.startswith("sk-YOUR")

# Базовая конфигурация для DeepSeek API
HEADERS = {
    "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
    "Content-Type": "application/json"
} if HAS_API_KEY else {}

async def make_ai_request(prompt: str, system_prompt: str = None, max_tokens: int = 2000) -> str:
    """Базовая функция для запросов к ИИ с увеличенным таймаутом."""
    
    # Если нет API ключа, используем mock
    if not HAS_API_KEY:
        return get_mock_response(prompt, system_prompt)
    
    messages = []
    
    if system_prompt:
        messages.append({
            "role": "system",
            "content": system_prompt
        })
    
    messages.append({
        "role": "user",
        "content": prompt
    })
    
    payload = {
        "model": "deepseek-chat",
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": 0.7,
        "top_p": 0.9,
        "stream": False  # Отключаем стриминг для стабильности
    }
    
    try:
        # Увеличенный таймаут до 120 секунд
        timeout = httpx.Timeout(
            timeout=120.0,  # Общий таймаут
            connect=30.0,   # Таймаут подключения
            read=90.0,      # Таймаут чтения
            write=30.0      # Таймаут записи
        )
        
        async with httpx.AsyncClient(timeout=timeout, verify=False) as client:
            print(f"🔄 Отправка запроса к DeepSeek API...")
            
            response = await client.post(
                f"{DEEPSEEK_BASE_URL}/v1/chat/completions",
                headers=HEADERS,
                json=payload
            )
            
            print(f"✅ Получен ответ: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                if 'choices' in result and len(result['choices']) > 0:
                    return result['choices'][0]['message']['content']
                else:
                    return "❌ Неожиданный формат ответа от API\n\n" + get_mock_response(prompt, system_prompt)
                    
            elif response.status_code == 401:
                return "❌ Ошибка авторизации. Проверьте API ключ.\n\n" + get_mock_response(prompt, system_prompt)
                
            elif response.status_code == 429:
                return "⚠️ Превышен лимит запросов. Попробуйте позже.\n\n" + get_mock_response(prompt, system_prompt)
                
            elif response.status_code == 400:
                error_detail = response.json().get('error', {}).get('message', 'Неизвестная ошибка')
                return f"❌ Ошибка запроса: {error_detail}\n\n" + get_mock_response(prompt, system_prompt)
                
            else:
                return f"❌ Ошибка API (код {response.status_code})\n\n" + get_mock_response(prompt, system_prompt)
                
    except httpx.TimeoutException as e:
        print(f"⏱ Таймаут: {e}")
        return "⏱ Превышено время ожидания (120 сек). Используется демо-режим.\n\n" + get_mock_response(prompt, system_prompt)
        
    except httpx.ConnectError as e:
        print(f"🌐 Ошибка подключения: {e}")
        return "🌐 Не удалось подключиться к API. Используется демо-режим.\n\n" + get_mock_response(prompt, system_prompt)
        
    except httpx.HTTPError as e:
        print(f"🔴 HTTP ошибка: {e}")
        return f"❌ Ошибка HTTP: {str(e)}\n\n" + get_mock_response(prompt, system_prompt)
        
    except json.JSONDecodeError as e:
        print(f"📄 Ошибка парсинга JSON: {e}")
        return "❌ Ошибка обработки ответа от API\n\n" + get_mock_response(prompt, system_prompt)
        
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {type(e).__name__}: {e}")
        return f"❌ Непредвиденная ошибка: {str(e)}\n\n" + get_mock_response(prompt, system_prompt)

def get_mock_response(prompt: str, system_prompt: str = None) -> str:
    """Возвращает заготовленные ответы когда API недоступен."""
    
    # Определяем тип запроса по ключевым словам
    prompt_lower = prompt.lower()
    
    if "взыскание" in prompt_lower or "неустойк" in prompt_lower or "судебн" in prompt_lower or "практик" in prompt_lower:
        return get_mock_legal_research_detailed()
    elif "договор" in prompt_lower:
        return get_mock_contract()
    elif "риск" in prompt_lower:
        return get_mock_risk_analysis()
    elif "финанс" in prompt_lower or "банкротств" in prompt_lower:
        return get_mock_financial_analysis()
    elif "документ" in prompt_lower:
        return get_mock_document_analysis()
    else:
        return get_mock_bankruptcy_analysis()

def get_mock_legal_research_detailed() -> str:
    """Детальный пример результата поиска судебной практики."""
    return """
📚 **АНАЛИЗ СУДЕБНОЙ ПРАКТИКИ**
_по теме: Взыскание неустойки по договору поставки_

**I. ПОЗИЦИЯ ВЕРХОВНОГО СУДА РФ:**

**1.** Определение ВС РФ от 14.03.2023 № 305-ЭС23-1876
• Неустойка подлежит снижению при явной несоразмерности
• Суд вправе снизить неустойку по ст. 333 ГК РФ
• Бремя доказывания несоразмерности - на должнике

**2.** Постановление Пленума ВС РФ от 24.03.2016 № 7
• П. 75: критерии снижения договорной неустойки
• П. 76: недопустимость полного освобождения от неустойки
• П. 77: учет финансового положения должника

**II. АРБИТРАЖНАЯ ПРАКТИКА:**

**Дело № А40-124525/2023** (АС Московского округа)
✅ Неустойка 0,1% в день признана разумной
📊 Снижена с 500 тыс. до 150 тыс. руб (в 3,3 раза)
📝 Учтено: частичное исполнение, тяжелое финансовое положение

**Дело № А56-89012/2023** (АС Северо-Западного округа)
❌ Отказано в снижении неустойки
📊 Должник не доказал несоразмерность
📝 Профессиональный участник рынка

**Дело № А33-15678/2023** (АС Восточно-Сибирского округа)
✅ Неустойка снижена судом по собственной инициативе
📊 С 1,2 млн до 400 тыс. руб
📝 Явная несоразмерность последствиям нарушения

**III. ПРИМЕНИМЫЕ НОРМЫ ПРАВА:**

• **ГК РФ ст. 330** - понятие неустойки
• **ГК РФ ст. 333** - уменьшение неустойки
• **ГК РФ ст. 506** - договор поставки
• **АПК РФ ст. 71** - оценка доказательств

**IV. СТАТИСТИКА РЕШЕНИЙ:**

По данным анализа 50 дел за 2023-2024:
• 68% - неустойка снижена
• 24% - оставлена без изменения
• 8% - взыскание отказано

Средний коэффициент снижения: 2,8 раза

**V. РЕКОМЕНДАЦИИ:**

✅ **Для кредитора:**
1. Обосновать размер убытков
2. Доказать умышленность нарушения
3. Показать платежеспособность должника

✅ **Для должника:**
1. Заявить о снижении по ст. 333 ГК
2. Предоставить финансовые документы
3. Доказать добросовестность действий

---
_Демо-версия анализа. API временно недоступен._
"""

def get_mock_contract() -> str:
    """Пример сгенерированного договора."""
    return """
**ДОГОВОР № ___/2024**
оказания юридических услуг по сопровождению процедуры банкротства

г. Москва                                                "___" _________ 2024 г.

**СТОРОНЫ ДОГОВОРА:**

Индивидуальный предприниматель ________________________,
именуемый в дальнейшем «Исполнитель», с одной стороны, и

Гражданин РФ _________________________________________________________,
именуемый в дальнейшем «Заказчик», с другой стороны,

заключили настоящий договор о нижеследующем:

**1. ПРЕДМЕТ ДОГОВОРА**

1.1. Исполнитель обязуется оказать Заказчику комплекс юридических услуг по сопровождению процедуры банкротства физического лица.

1.2. Услуги включают:
• Правовой анализ ситуации
• Подготовку документов для суда
• Представительство в суде
• Взаимодействие с управляющим

**2. СТОИМОСТЬ И ОПЛАТА**

2.1. Стоимость услуг: __________ рублей
2.2. Порядок оплаты: 50% предоплата, 50% после подачи заявления

**3. ПРАВА И ОБЯЗАННОСТИ**

3.1. Исполнитель обязуется оказать услуги качественно и в срок
3.2. Заказчик обязуется предоставить необходимые документы

**4. РЕКВИЗИТЫ СТОРОН**

ИСПОЛНИТЕЛЬ:                           ЗАКАЗЧИК:
_____________________                  _____________________

---
_Демо-версия договора_
"""

def get_mock_risk_analysis() -> str:
    """Пример анализа рисков."""
    return """
⚠️ **АНАЛИЗ ПРАВОВЫХ РИСКОВ**

**Общий уровень риска:** СРЕДНИЙ (5.5/10)

**Правовые риски:**
• Риск отказа в признании банкротом: НИЗКИЙ (20%)
• Риск оспаривания сделок: СРЕДНИЙ (40%)
• Риск непризнания долгов: НИЗКИЙ (25%)

**Финансовые риски:**
• Потеря имущества (кроме единственного жилья)
• Расходы на процедуру: 60-80 тыс. руб
• Ограничение кредитования на 5 лет

**Рекомендации:**
✅ Полное раскрытие информации суду
✅ Документальное подтверждение всех операций
✅ Сотрудничество с финансовым управляющим

---
_Демо-версия анализа_
"""

def get_mock_financial_analysis() -> str:
    """Пример финансового анализа."""
    return """
💼 **ФИНАНСОВЫЙ АНАЛИЗ**

**Признаки банкротства:**
✅ Долг превышает 500 000 руб
✅ Просрочка платежей более 3 месяцев
✅ Невозможность исполнения обязательств

**Анализ платежеспособности:**
• Коэффициент текущей ликвидности: 0.3 (критический)
• Долговая нагрузка: 85% от дохода
• Прогноз погашения: невозможно

**Рекомендация:**
Процедура банкротства целесообразна

**Оптимальная процедура:**
Реализация имущества (6-8 месяцев)

---
_Демо-версия анализа_
"""

def get_mock_document_analysis() -> str:
    """Пример анализа документа."""
    return """
📄 **АНАЛИЗ ДОКУМЕНТА**

**Выявленные проблемы:**
⚠️ Завышенная неустойка (2% в день)
⚠️ Скрытые комиссии
⚠️ Навязанная страховка

**Возможности для оспаривания:**
✅ Снижение неустойки по ст. 333 ГК РФ
✅ Возврат страховки по ст. 958 ГК РФ
✅ Отмена незаконных комиссий

**Потенциальная экономия:** до 150 000 руб

---
_Демо-версия анализа_
"""

def get_mock_bankruptcy_analysis() -> str:
    """Стандартный анализ банкротства."""
    return """
📊 **ЭКСПРЕСС-АНАЛИЗ СИТУАЦИИ**

✅ **Процедура банкротства рекомендована**

**Основания:**
• Долг превышает 500 000 руб
• Просрочка более 3 месяцев
• Доход недостаточен для погашения

**Рекомендуемая процедура:**
Реализация имущества (6-8 месяцев)

**Стоимость:**
• Госпошлина: 300 руб
• Управляющий: 25 000 руб
• Публикации: 15 000 руб
• Юрист: 45-60 000 руб
• **Итого:** 85-100 000 руб

**Последствия:**
✅ Списание долгов
⚠️ Ограничения на 3-5 лет

---
_Демо-версия анализа_
"""

# Основные функции
async def analyze_bankruptcy_case(debt_amount: int, income: int, description: str) -> str:
    """Анализирует кейс банкротства с помощью ИИ."""
    
    system_prompt = """Ты опытный юрист по банкротству физических лиц в России. 
    Анализируй ситуации клиентов и давай рекомендации основываясь на ФЗ-127 "О несостоятельности (банкротстве)".
    Отвечай на русском языке, структурированно."""
    
    prompt = f"""
    Проанализируй ситуацию клиента:
    - Сумма долга: {debt_amount:,} руб.
    - Доход: {income:,} руб.
    - Описание: {description}
    
    Дай краткий анализ и рекомендации.
    """
    
    return await make_ai_request(prompt, system_prompt)

async def chat_with_ai(message: str, context: Dict = None) -> str:
    """Чат с ИИ-юристом."""
    
    system_prompt = """Ты квалифицированный юрист-консультант по банкротству физических лиц в России.
    Отвечай кратко, по существу, ссылаясь на законодательство.
    Отвечай на русском языке."""
    
    return await make_ai_request(message, system_prompt, max_tokens=1000)

async def analyze_document_with_ai(document_text: str) -> str:
    """Анализирует юридический документ."""
    
    system_prompt = """Ты опытный юрист. Анализируй документы, выявляй риски и проблемы.
    Отвечай на русском языке, структурированно."""
    
    prompt = f"Проанализируй документ:\n{document_text[:3000]}"
    
    return await make_ai_request(prompt, system_prompt, max_tokens=2000)

async def generate_contract_with_ai(contract_params: str) -> str:
    """Генерирует договор по заданным параметрам."""
    
    system_prompt = """Ты юрист, составляющий договоры по российскому праву.
    Составляй юридически грамотные договоры.
    Пиши на русском языке."""
    
    return await make_ai_request(contract_params, system_prompt, max_tokens=3000)

async def legal_research_with_ai(query: str) -> str:
    """Поиск и анализ судебной практики."""
    
    system_prompt = """Ты юридический исследователь российского права.
    Анализируй судебную практику, приводи примеры решений судов.
    Отвечай на русском языке, структурированно."""
    
    prompt = f"Найди и проанализируй судебную практику по теме: {query}"
    
    return await make_ai_request(prompt, system_prompt, max_tokens=2500)

async def analyze_risks_with_ai(situation: str) -> str:
    """Анализирует правовые риски."""
    
    system_prompt = """Ты риск-менеджер и юрист. Анализируй правовые риски.
    Оценивай вероятность негативных последствий.
    Отвечай на русском языке."""
    
    return await make_ai_request(situation, system_prompt, max_tokens=2000)

async def analyze_financial_documents(financial_data: str) -> str:
    """Анализирует финансовые документы на признаки банкротства."""
    
    system_prompt = """Ты финансовый аналитик и юрист по банкротству.
    Анализируй финансовые показатели на признаки несостоятельности.
    Отвечай на русском языке."""
    
    prompt = f"Проанализируй финансовые данные на признаки банкротства:\n{financial_data}"
    
    return await make_ai_request(prompt, system_prompt, max_tokens=2000)

# Проверка конфигурации при импорте
if HAS_API_KEY:
    print(f"✅ DeepSeek API сконфигурирован (ключ: ...{DEEPSEEK_API_KEY[-8:]})")
else:
    print("⚠️ DeepSeek API не настроен, используются демо-ответы")
