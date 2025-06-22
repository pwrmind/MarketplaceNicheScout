import time
import random
import heapq
import json
import uuid
from dataclasses import dataclass, asdict, field
from typing import List, Dict, Optional, Tuple, Any
from collections import defaultdict

# ================== Модели данных ==================
@dataclass
class CategoryData:
    id: str
    name: str
    monthly_sales: int
    avg_price: float
    competition_score: float
    trend_score: float = 0.0

@dataclass
class NicheEvaluation:
    category_id: str
    category_name: str  # Исправление: Добавлено название категории
    profitability_score: float
    risk_score: float
    compliance_ok: bool

@dataclass
class Recommendation:
    category_id: str
    category_name: str
    confidence: float
    reasons: List[str]

@dataclass
class Persona:
    persona_type: str
    age_range: List[int]
    buying_factors: List[str]
    pain_points: List[str]

# ================== GOAP Core ==================
class Action:
    def __init__(self, name: str, preconditions: Dict[str, Any], effects: Dict[str, Any], cost: float = 1.0):
        self.name = name
        self.preconditions = preconditions
        self.effects = effects
        self.cost = cost

    def __repr__(self):
        return f"Action({self.name})"

class Node:
    def __init__(self, state: Dict[str, Any], actions: List[Action], cost: float):
        self.state = state
        self.actions = actions
        self.cost = cost

    def __lt__(self, other):
        return self.cost < other.cost

class GOAPPlanner:
    def plan(self, actions: List[Action], goals: Dict[str, Any], state: Dict[str, Any]) -> List[Action]:
        frontier = []
        heapq.heappush(frontier, Node(state.copy(), [], 0))
        explored = set()
        while frontier:
            node = heapq.heappop(frontier)
            if self.goals_satisfied(goals, node.state):
                return node.actions
            state_hash = self.state_hash(node.state)
            if state_hash in explored:
                continue
            explored.add(state_hash)
            for action in actions:
                if self.can_perform(action, node.state):
                    new_state = self.apply_effects(action, node.state.copy())
                    new_cost = node.cost + action.cost
                    new_actions = node.actions + [action]
                    heapq.heappush(
                        frontier, 
                        Node(new_state, new_actions, new_cost)
                    )
        return []  # План не найден

    def can_perform(self, action: Action, state: Dict[str, Any]) -> bool:
        for key, value in action.preconditions.items():
            if key not in state or state[key] != value:
                return False
        return True

    def apply_effects(self, action: Action, state: Dict[str, Any]) -> Dict[str, Any]:
        for key, value in action.effects.items():
            state[key] = value
        return state

    def goals_satisfied(self, goals: Dict[str, Any], state: Dict[str, Any]) -> bool:
        for key, value in goals.items():
            if key not in state or state[key] != value:
                return False
        return True

    def state_hash(self, state: Dict[str, Any]) -> str:
        return json.dumps(state, sort_keys=True)

# ================== Message Broker ==================
class MessageBroker:
    def __init__(self):
        self.queues = defaultdict(list)
        self.subscribers = defaultdict(list)

    def publish(self, queue: str, message: dict):
        self.queues[queue].append(message)
        for callback in self.subscribers[queue]:
            callback(message)

    def consume(self, queue: str) -> Optional[dict]:
        return self.queues[queue].pop(0) if self.queues[queue] else None

    def subscribe(self, queue: str, callback):
        self.subscribers[queue].append(callback)

# ================== Robots ==================
class DataCollector:
    def __init__(self, broker: MessageBroker):
        self.broker = broker
        self.categories = [
            "Электроника", "Дом и сад", "Красота", 
            "Одежда", "Детские товары", "Автотовары"
        ]
        self.planner = GOAPPlanner()
        self.state = {
            "api_available": True,
            "catalog_accessible": True,
            "has_category_sales": False,
            "has_price_data": False,
            "has_seller_count": False
        }
        self.actions = [
            Action(
                name="fetch_sales_data",
                preconditions={"api_available": True},
                effects={"has_category_sales": True},
                cost=1.0
            ),
            Action(
                name="scrape_prices",
                preconditions={"catalog_accessible": True},
                effects={"has_price_data": True},
                cost=1.5
            ),
            Action(
                name="count_sellers",
                preconditions={"catalog_accessible": True},
                effects={"has_seller_count": True},
                cost=2.0
            ),
            Action(
                name="fallback_api_scraping",
                preconditions={"api_available": False, "catalog_accessible": True},
                effects={"has_category_sales": True, "has_price_data": True},
                cost=3.0
            )
        ]
        self.goals = {
            "has_category_sales": True,
            "has_price_data": True,
            "has_seller_count": True
        }

    def collect_data(self):
        print("\n[Data Collector] Planning data collection...")
        plan = self.planner.plan(self.actions, self.goals, self.state)
        if not plan:
            print("No valid plan found!")
            return
        print(f"Execution plan: {[a.name for a in plan]}")
        for action in plan:
            print(f"Executing: {action.name}")
            time.sleep(0.5)
            if action.name == "fetch_sales_data":
                self.fetch_sales_from_api()
            elif action.name == "scrape_prices":
                self.scrape_price_data()
            elif action.name == "count_sellers":
                self.count_sellers()
            elif action.name == "fallback_api_scraping":
                self.fallback_scraping()
        self.publish_data()

    def fetch_sales_from_api(self):
        print("Fetching sales data from API...")
        self.state["has_category_sales"] = True

    def scrape_price_data(self):
        print("Scraping price data from catalog...")
        self.state["has_price_data"] = True

    def count_sellers(self):
        print("Counting sellers in categories...")
        self.state["has_seller_count"] = True

    def fallback_scraping(self):
        print("Using fallback scraping method...")
        self.state["has_category_sales"] = True
        self.state["has_price_data"] = True

    def publish_data(self):
        data = []
        for cat_id, name in enumerate(self.categories):
            data.append(CategoryData(
                id=f"cat_{cat_id}",
                name=name,
                monthly_sales=random.randint(500, 5000),
                avg_price=random.uniform(10, 500),
                competition_score=random.uniform(0.1, 0.9)
            ))
        self.broker.publish("market.raw_data", {
            "event_id": str(uuid.uuid4()),
            "platform": "wildberries",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "categories": [asdict(d) for d in data]
        })

class AnalyticsEngine:
    def __init__(self, broker: MessageBroker):
        self.broker = broker
        self.planner = GOAPPlanner()
        self.state = {
            "raw_data_received": False,
            "data_parsed": False,  # Исправление: Добавлено состояние data_parsed
            "demand_calculated": False,
            "trends_identified": False
        }
        self.actions = [
            Action(
                name="parse_raw_data",
                preconditions={"raw_data_received": True},
                effects={"data_parsed": True},
                cost=1.0
            ),
            Action(
                name="calculate_demand",
                preconditions={"data_parsed": True},
                effects={"demand_calculated": True},
                cost=2.0
            ),
            Action(
                name="analyze_trends",
                preconditions={"data_parsed": True},
                effects={"trends_identified": True},
                cost=3.0
            )
        ]
        self.goals = {
            "demand_calculated": True,
            "trends_identified": True
        }
        broker.subscribe("market.raw_data", self.handle_raw_data)

    def handle_raw_data(self, message):
        print("\n[Analytics Engine] Received raw data")
        self.state["raw_data_received"] = True
        self.process_data(message)

    def process_data(self, message):
        print("Planning data processing...")
        plan = self.planner.plan(self.actions, self.goals, self.state)
        if not plan:
            print("No valid plan found!")
            return
        print(f"Execution plan: {[a.name for a in plan]}")
        categories = [CategoryData(**item) for item in message["categories"]]
        for action in plan:
            print(f"Executing: {action.name}")
            time.sleep(0.5)
            if action.name == "parse_raw_data":
                self.state["data_parsed"] = True
            elif action.name == "calculate_demand":
                demand_scores = {}
                for category in categories:
                    # Исправление: Удаление случайности, добавлена детерминированная формула
                    demand_factor = 1.0 + (category.monthly_sales / 1000)
                    demand_scores[category.id] = (category.monthly_sales * demand_factor) / max(category.competition_score, 0.01)
                self.demand_scores = demand_scores
                self.state["demand_calculated"] = True
            elif action.name == "analyze_trends":
                for category in categories:
                    # Исправление: Детерминированный расчет тренда
                    if "Электроника" in category.name:
                        category.trend_score = 0.9
                    elif "Дом" in category.name:
                        category.trend_score = 0.7
                    else:
                        category.trend_score = 0.5
                self.categories = categories
                self.state["trends_identified"] = True
        self.publish_results(message["event_id"])

    def publish_results(self, event_id):
        self.broker.publish("market.analyzed_data", {
            "correlation_id": event_id,
            "demand_scores": self.demand_scores,
            "categories": [asdict(c) for c in self.categories]
        })

class AudienceResearch:
    def __init__(self, broker: MessageBroker):
        self.broker = broker
        broker.subscribe("market.analyzed_data", self.handle_analyzed_data)

    def handle_analyzed_data(self, message):
        print("\n[Audience Research] Received analyzed data")
        categories = [CategoryData(**item) for item in message["categories"]]
        for category in categories:
            self.analyze_category(category)

    def analyze_category(self, category):
        print(f"Analyzing audience for {category.name}")
        time.sleep(0.3)
        personas = [
            Persona(
                persona_type="tech_enthusiast",
                age_range=[25, 40],
                buying_factors=["innovation", "brand"],
                pain_points=["compatibility", "setup_complexity"]
            )
        ] if "Электроника" in category.name else [
            Persona(
                persona_type="home_improver",
                age_range=[30, 55],
                buying_factors=["quality", "durability"],
                pain_points=["assembly", "space"]
            )
        ]
        self.broker.publish("audience.insights", {
            "category_id": category.id,
            "audience_score": 0.8,  # Исправление: Удаление случайности
            "personas": [asdict(p) for p in personas]
        })

class NicheEvaluator:
    def __init__(self, broker: MessageBroker):
        self.broker = broker
        self.planner = GOAPPlanner()
        self.state = {
            "category_data_ready": False,
            "audience_data_ready": False,
            "niche_evaluated": False
        }
        self.category_data = {}
        self.audience_data = {}
        self.expected_categories = set()  # Исправление: Для отслеживания ожидаемых категорий
        self.compliance_rules = {  # Исправление: Гибкие правила соответствия
            "Детские товары": True,  # По умолчанию разрешено
            "Автотовары": True
        }
        broker.subscribe("market.analyzed_data", self.handle_analyzed_data)
        broker.subscribe("audience.insights", self.handle_audience_data)

    def handle_analyzed_data(self, message):
        print("\n[Niche Evaluator] Received analyzed data")
        self.category_data = {}
        for item in message["categories"]:
            cat = CategoryData(**item)
            self.category_data[cat.id] = cat
        self.expected_categories = set(self.category_data.keys())  # Исправление: Отслеживание всех категорий
        self.state["category_data_ready"] = True
        self.try_evaluate()

    def handle_audience_data(self, message):
        print(f"[Niche Evaluator] Received audience data for {message['category_id']}")
        self.audience_data[message["category_id"]] = message
        # Исправление: Проверка полноты данных
        if set(self.audience_data.keys()) == self.expected_categories:
            self.state["audience_data_ready"] = True
            self.try_evaluate()

    def try_evaluate(self):
        if not self.state["category_data_ready"] or not self.state["audience_data_ready"]:
            return
        plan = self.planner.plan([
            Action(
                name="evaluate_category",
                preconditions={"category_data_ready": True, "audience_data_ready": True},
                effects={"niche_evaluated": True},
                cost=1.0
            )
        ], {"niche_evaluated": True}, self.state)
        if plan:
            self.evaluate_categories()

    def evaluate_categories(self):
        print("\n[Niche Evaluator] Evaluating niches...")
        evaluations = []
        for cat_id, category in self.category_data.items():
            if cat_id not in self.audience_data:
                continue
            audience = self.audience_data[cat_id]
            audience_score = audience["audience_score"]
            profitability = (category.monthly_sales * category.avg_price * 0.2) * audience_score
            risk = 1 - category.trend_score
            compliance = self.compliance_rules.get(category.name, True)
            evaluations.append(NicheEvaluation(
                category_id=cat_id,
                category_name=category.name,  # Исправление: Передача названия
                profitability_score=profitability,
                risk_score=risk,
                compliance_ok=compliance
            ))
        self.broker.publish("niche.evaluations", {
            "evaluations": [asdict(e) for e in evaluations]
        })

class DecisionMaker:
    def __init__(self, broker: MessageBroker):
        self.broker = broker
        broker.subscribe("niche.evaluations", self.handle_evaluations)

    def handle_evaluations(self, message):
        print("\n[Decision Maker] Received niche evaluations")
        evaluations = [NicheEvaluation(**item) for item in message["evaluations"]]
        valid_niches = [e for e in evaluations if e.compliance_ok]
        
        if not valid_niches:
            recommendation = Recommendation(
                category_id="none",
                category_name="Нет подходящих ниш",
                confidence=0.0,
                reasons=["Ни одна категория не соответствует правилам маркетплейса"]
            )
        else:
            best_niche = max(valid_niches, key=lambda x: x.profitability_score / max(x.risk_score, 0.01))
            # Исправление: Использование названия из оценки
            recommendation = Recommendation(
                category_id=best_niche.category_id,
                category_name=best_niche.category_name,
                confidence=min(best_niche.profitability_score / 10000, 1.0),
                reasons=[
                    f"Высокая прибыльность ({best_niche.profitability_score:.1f})",
                    f"Низкий риск ({best_niche.risk_score:.2f})",
                    f"Соответствие правилам платформы"
                ]
            )
        self.broker.publish("niche.recommendation", asdict(recommendation))

# ================== Global Orchestrator ==================
class Orchestrator:
    def __init__(self, broker: MessageBroker):
        self.broker = broker
        self.planner = GOAPPlanner()
        self.state = {
            "data_collected": False,
            "data_analyzed": False,
            "audience_analyzed": False,
            "niches_evaluated": False,
            "decision_made": False
        }
        # Глобальные действия
        self.actions = [
            Action(
                name="collect_data",
                preconditions={},
                effects={"data_collected": True},
                cost=1.0
            ),
            Action(
                name="analyze_data",
                preconditions={"data_collected": True},
                effects={"data_analyzed": True},
                cost=2.0
            ),
            Action(
                name="research_audience",
                preconditions={"data_analyzed": True},
                effects={"audience_analyzed": True},
                cost=1.5
            ),
            Action(
                name="evaluate_niches",
                preconditions={"data_analyzed": True, "audience_analyzed": True},
                effects={"niches_evaluated": True},
                cost=3.0
            ),
            Action(
                name="make_decision",
                preconditions={"niches_evaluated": True},
                effects={"decision_made": True},
                cost=1.0
            )
        ]
        # Подписки на события
        broker.subscribe("market.raw_data", lambda _: self.update_state("data_collected", True))
        broker.subscribe("market.analyzed_data", lambda _: self.update_state("data_analyzed", True))
        broker.subscribe("audience.insights", lambda _: self.update_state("audience_analyzed", True))
        broker.subscribe("niche.evaluations", lambda _: self.update_state("niches_evaluated", True))
        broker.subscribe("niche.recommendation", lambda _: self.update_state("decision_made", True))

    def update_state(self, key, value):
        # Исправление: Проверка полноты данных
        if key == "data_collected" and value:
            # В реальном приложении здесь должна быть проверка успешности сбора данных
            pass
        self.state[key] = value
        self.run_workflow()

    def run_workflow(self):
        print("\n[Orchestrator] Current state:", self.state)
        # Цели системы
        goals = {"decision_made": True}
        # Если цель уже достигнута
        if self.planner.goals_satisfied(goals, self.state):
            print("Goal already achieved!")
            return
        plan = self.planner.plan(self.actions, goals, self.state)
        if not plan:
            print("No valid global plan found!")
            return
        print(f"Global execution plan: {[a.name for a in plan]}")
        # В реальной системе здесь был бы вызов соответствующих сервисов
        for action in plan:
            print(f"Triggering: {action.name}")
            # Вместо реального вызова просто публикуем событие
            if action.name == "collect_data":
                self.broker.publish("orchestrator.command", {"command": "collect_data"})
            elif action.name == "analyze_data":
                self.broker.publish("orchestrator.command", {"command": "analyze_data"})
            elif action.name == "research_audience":
                self.broker.publish("orchestrator.command", {"command": "research_audience"})
            elif action.name == "evaluate_niches":
                self.broker.publish("orchestrator.command", {"command": "evaluate_niches"})
            elif action.name == "make_decision":
                self.broker.publish("orchestrator.command", {"command": "make_decision"})

# ================== Main ==================
def main():
    # Инициализация брокера сообщений
    broker = MessageBroker()
    # Создание роботов
    collector = DataCollector(broker)
    analytics = AnalyticsEngine(broker)
    audience_research = AudienceResearch(broker)
    evaluator = NicheEvaluator(broker)
    decision_maker = DecisionMaker(broker)
    # Создание оркестратора
    orchestrator = Orchestrator(broker)
    # Подписка роботов на команды оркестратора
    broker.subscribe("orchestrator.command", lambda msg: handle_orchestrator_command(msg, collector))
    # Запуск процесса
    print("=== Starting niche selection process ===")
    orchestrator.run_workflow()
    # Ожидание завершения
    time.sleep(5)
    # Вывод результата
    recommendation = broker.consume("niche.recommendation")
    if recommendation:
        print("\n=== FINAL RECOMMENDATION ===")
        print(f"Category: {recommendation['category_name']}")
        print(f"Confidence: {recommendation['confidence']:.2%}")
        print("Reasons:")
        for reason in recommendation['reasons']:
            print(f" - {reason}")
    else:
        print("\nNo recommendation received")

def handle_orchestrator_command(message, collector):
    command = message["command"]
    if command == "collect_data":
        collector.collect_data()

if __name__ == "__main__":
    main()