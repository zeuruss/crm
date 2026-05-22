from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
import json
from pathlib import Path
from typing import Dict, List, Optional


DATA_FILE_NAME = "crm_data.json"


@dataclass
class Product:
    """Товар из каталога."""

    product_id: int
    name: str
    purchase_price: float
    sale_price: float

    def to_dict(self) -> dict:
        """Преобразовать товар в словарь для JSON."""
        return {
            "id": self.product_id,
            "name": self.name,
            "purchase_price": self.purchase_price,
            "sale_price": self.sale_price,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Product":
        """Создать товар из данных JSON."""
        return cls(
            product_id=int(data["id"]),
            name=str(data["name"]),
            purchase_price=float(data["purchase_price"]),
            sale_price=float(data["sale_price"]),
        )


class Person:
    """Базовый класс для людей."""

    def __init__(self, person_id: int, name: str, phone: str) -> None:
        self._id = person_id
        self._name = name.strip()
        self._phone = phone.strip()

    @property
    def person_id(self) -> int:
        """Вернуть идентификатор."""
        return self._id

    @property
    def name(self) -> str:
        """Вернуть имя."""
        return self._name

    @property
    def phone(self) -> str:
        """Вернуть телефон."""
        return self._phone


class Employee(Person):
    """Сотрудник компании."""

    def __init__(self, person_id: int, name: str, phone: str, position: str) -> None:
        super().__init__(person_id, name, phone)
        self._position = position.strip()

    @property
    def position(self) -> str:
        """Вернуть должность."""
        return self._position

    def to_dict(self) -> dict:
        """Преобразовать сотрудника в словарь для JSON."""
        return {
            "id": self.person_id,
            "name": self.name,
            "phone": self.phone,
            "position": self.position,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Employee":
        """Создать сотрудника из данных JSON."""
        return cls(
            person_id=int(data["id"]),
            name=str(data["name"]),
            phone=str(data["phone"]),
            position=str(data.get("position", "")),
        )


class Customer(Person):
    """Покупатель компании."""

    def to_dict(self) -> dict:
        """Преобразовать покупателя в словарь для JSON."""
        return {
            "id": self.person_id,
            "name": self.name,
            "phone": self.phone,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Customer":
        """Создать покупателя из данных JSON."""
        return cls(
            person_id=int(data["id"]),
            name=str(data["name"]),
            phone=str(data.get("phone", "")),
        )


class WarehouseCell:
    """Ячейка склада для хранения товара."""

    def __init__(
        self,
        cell_id: int,
        capacity: int,
        inventory: Optional[Dict[int, int]] = None,
    ) -> None:
        self._id = cell_id
        self._capacity = capacity
        self._inventory: Dict[int, int] = inventory or {}

    @property
    def cell_id(self) -> int:
        """Вернуть идентификатор ячейки."""
        return self._id

    @property
    def capacity(self) -> int:
        """Вернуть вместимость ячейки."""
        return self._capacity

    def used_capacity(self) -> int:
        """Вернуть занятое место."""
        return sum(self._inventory.values())

    def available_capacity(self) -> int:
        """Вернуть свободное место."""
        return self.capacity - self.used_capacity()

    def inventory_items(self) -> Dict[int, int]:
        """Вернуть копию запасов ячейки."""
        return dict(self._inventory)

    def add_product(self, product_id: int, quantity: int) -> None:
        """Положить товар в ячейку."""
        if quantity <= 0:
            raise ValueError("количество должно быть положительным")

        if self.available_capacity() < quantity:
            raise ValueError("превышена вместимость ячейки")

        self._inventory[product_id] = self._inventory.get(product_id, 0) + quantity

    def remove_product(self, product_id: int, quantity: int) -> None:
        """Взять товар из ячейки."""
        if quantity <= 0:
            raise ValueError("количество должно быть положительным")

        current = self._inventory.get(product_id, 0)

        if current < quantity:
            raise ValueError("недостаточно товара в ячейке")

        remaining = current - quantity

        if remaining:
            self._inventory[product_id] = remaining
        else:
            self._inventory.pop(product_id, None)

    def to_dict(self) -> dict:
        """Преобразовать ячейку в словарь для JSON."""
        return {
            "id": self.cell_id,
            "capacity": self.capacity,
            "inventory": _int_dict_to_json(self._inventory),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "WarehouseCell":
        """Создать ячейку из данных JSON."""
        inventory = _json_dict_to_int(data.get("inventory", {}))

        return cls(
            cell_id=int(data["id"]),
            capacity=int(data["capacity"]),
            inventory=inventory,
        )


class StorageLocation(ABC):
    """Базовый класс для склада и пункта продаж."""

    def __init__(
        self,
        location_id: int,
        name: str,
        responsible_id: Optional[int],
    ) -> None:
        self._id = location_id
        self._name = name.strip()
        self._responsible_id = responsible_id

    @property
    def location_id(self) -> int:
        """Вернуть идентификатор объекта."""
        return self._id

    @property
    def name(self) -> str:
        """Вернуть название объекта."""
        return self._name

    @property
    def responsible_id(self) -> Optional[int]:
        """Вернуть id ответственного сотрудника."""
        return self._responsible_id

    @responsible_id.setter
    def responsible_id(self, employee_id: Optional[int]) -> None:
        """Назначить нового ответственного."""
        self._responsible_id = employee_id

    @abstractmethod
    def location_type(self) -> str:
        """Вернуть тип объекта."""
        raise NotImplementedError

    @abstractmethod
    def inventory_items(self) -> Dict[int, int]:
        """Вернуть текущие запасы."""
        raise NotImplementedError

    @abstractmethod
    def add_stock(
        self,
        product_id: int,
        quantity: int,
        cell_id: Optional[int] = None,
    ) -> None:
        """Добавить товар."""
        raise NotImplementedError

    @abstractmethod
    def remove_stock(
        self,
        product_id: int,
        quantity: int,
        cell_id: Optional[int] = None,
    ) -> None:
        """Убрать товар."""
        raise NotImplementedError

    def summary(self) -> str:
        """Вернуть краткую строку об объекте."""
        return f"{self.location_type()} #{self.location_id}: {self.name}"


class Warehouse(StorageLocation):
    """Склад с набором ячеек."""

    def __init__(
        self,
        location_id: int,
        name: str,
        responsible_id: Optional[int],
        cells: Optional[Dict[int, WarehouseCell]] = None,
    ) -> None:
        super().__init__(location_id, name, responsible_id)
        self._cells: Dict[int, WarehouseCell] = cells or {}

    def location_type(self) -> str:
        """Вернуть тип объекта."""
        return "склад"

    def cells(self) -> Dict[int, WarehouseCell]:
        """Вернуть копию списка ячеек."""
        return dict(self._cells)

    def add_cell(self, capacity: int) -> WarehouseCell:
        """Добавить ячейку на склад."""
        if capacity <= 0:
            raise ValueError("вместимость должна быть положительной")

        next_id = max(self._cells.keys(), default=0) + 1
        cell = WarehouseCell(next_id, capacity)
        self._cells[next_id] = cell

        return cell

    def get_cell(self, cell_id: int) -> WarehouseCell:
        """Вернуть ячейку по id."""
        return self._cells[cell_id]

    def inventory_items(self) -> Dict[int, int]:
        """Вернуть общий список запасов склада."""
        total: Dict[int, int] = {}

        for cell in self._cells.values():
            for product_id, qty in cell.inventory_items().items():
                total[product_id] = total.get(product_id, 0) + qty

        return total

    def add_stock(
        self,
        product_id: int,
        quantity: int,
        cell_id: Optional[int] = None,
    ) -> None:
        """Добавить товар в указанную ячейку."""
        if cell_id is None:
            raise ValueError("для склада нужно указать ячейку")

        self.get_cell(cell_id).add_product(product_id, quantity)

    def remove_stock(
        self,
        product_id: int,
        quantity: int,
        cell_id: Optional[int] = None,
    ) -> None:
        """Убрать товар из указанной ячейки."""
        if cell_id is None:
            raise ValueError("для склада нужно указать ячейку")

        self.get_cell(cell_id).remove_product(product_id, quantity)

    def to_dict(self) -> dict:
        """Преобразовать склад в словарь для JSON."""
        return {
            "id": self.location_id,
            "name": self.name,
            "responsible_id": self.responsible_id,
            "cells": [cell.to_dict() for cell in self._cells.values()],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Warehouse":
        """Создать склад из данных JSON."""
        cells = {
            int(cell["id"]): WarehouseCell.from_dict(cell)
            for cell in data.get("cells", [])
        }

        return cls(
            location_id=int(data["id"]),
            name=str(data["name"]),
            responsible_id=_optional_int(data.get("responsible_id")),
            cells=cells,
        )


class SalesPoint(StorageLocation):
    """Пункт продаж для хранения товара."""

    def __init__(
        self,
        location_id: int,
        name: str,
        responsible_id: Optional[int],
        inventory: Optional[Dict[int, int]] = None,
    ) -> None:
        super().__init__(location_id, name, responsible_id)
        self._inventory: Dict[int, int] = inventory or {}

    def location_type(self) -> str:
        """Вернуть тип объекта."""
        return "пункт продаж"

    def inventory_items(self) -> Dict[int, int]:
        """Вернуть текущие запасы пункта продаж."""
        return dict(self._inventory)

    def add_stock(
        self,
        product_id: int,
        quantity: int,
        cell_id: Optional[int] = None,
    ) -> None:
        """Добавить товар в пункт продаж."""
        if quantity <= 0:
            raise ValueError("количество должно быть положительным")

        self._inventory[product_id] = self._inventory.get(product_id, 0) + quantity

    def remove_stock(
        self,
        product_id: int,
        quantity: int,
        cell_id: Optional[int] = None,
    ) -> None:
        """Убрать товар из пункта продаж."""
        if quantity <= 0:
            raise ValueError("количество должно быть положительным")

        current = self._inventory.get(product_id, 0)

        if current < quantity:
            raise ValueError("недостаточно товара")

        remaining = current - quantity

        if remaining:
            self._inventory[product_id] = remaining
        else:
            self._inventory.pop(product_id, None)

    def to_dict(self) -> dict:
        """Преобразовать пункт продаж в словарь для JSON."""
        return {
            "id": self.location_id,
            "name": self.name,
            "responsible_id": self.responsible_id,
            "inventory": _int_dict_to_json(self._inventory),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SalesPoint":
        """Создать пункт продаж из данных JSON."""
        inventory = _json_dict_to_int(data.get("inventory", {}))

        return cls(
            location_id=int(data["id"]),
            name=str(data["name"]),
            responsible_id=_optional_int(data.get("responsible_id")),
            inventory=inventory,
        )


@dataclass
class Order:
    """Заказ на закупку, продажу или возврат."""

    order_id: int
    kind: str
    product_id: int
    quantity: int
    unit_price: float
    amount: float
    customer_id: Optional[int]
    sales_point_id: Optional[int]
    warehouse_id: Optional[int]
    created_at: str

    def to_dict(self) -> dict:
        """Преобразовать заказ в словарь для JSON."""
        return {
            "id": self.order_id,
            "kind": self.kind,
            "product_id": self.product_id,
            "quantity": self.quantity,
            "unit_price": self.unit_price,
            "amount": self.amount,
            "customer_id": self.customer_id,
            "sales_point_id": self.sales_point_id,
            "warehouse_id": self.warehouse_id,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Order":
        """Создать заказ из данных JSON."""
        return cls(
            order_id=int(data["id"]),
            kind=str(data["kind"]),
            product_id=int(data["product_id"]),
            quantity=int(data["quantity"]),
            unit_price=float(data["unit_price"]),
            amount=float(data["amount"]),
            customer_id=_optional_int(data.get("customer_id")),
            sales_point_id=_optional_int(data.get("sales_point_id")),
            warehouse_id=_optional_int(data.get("warehouse_id")),
            created_at=str(data.get("created_at", "")),
        )


@dataclass
class CRM:
    """Все данные CRM в памяти."""

    products: Dict[int, Product] = field(default_factory=dict)
    employees: Dict[int, Employee] = field(default_factory=dict)
    customers: Dict[int, Customer] = field(default_factory=dict)
    warehouses: Dict[int, Warehouse] = field(default_factory=dict)
    sales_points: Dict[int, SalesPoint] = field(default_factory=dict)
    orders: List[Order] = field(default_factory=list)
    next_ids: Dict[str, int] = field(
        default_factory=lambda: {
            "product": 1,
            "employee": 1,
            "customer": 1,
            "warehouse": 1,
            "sales_point": 1,
            "order": 1,
        }
    )

    def next_id(self, key: str) -> int:
        """Вернуть следующий id для типа."""
        current = self.next_ids.get(key, 1)
        self.next_ids[key] = current + 1

        return current

    def to_dict(self) -> dict:
        """Преобразовать данные CRM в словарь для JSON."""
        return {
            "products": [item.to_dict() for item in self.products.values()],
            "employees": [item.to_dict() for item in self.employees.values()],
            "customers": [item.to_dict() for item in self.customers.values()],
            "warehouses": [item.to_dict() for item in self.warehouses.values()],
            "sales_points": [item.to_dict() for item in self.sales_points.values()],
            "orders": [item.to_dict() for item in self.orders],
            "next_ids": dict(self.next_ids),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CRM":
        """Создать CRM из данных JSON."""
        instance = cls()
        instance.products = {
            item["id"]: Product.from_dict(item) for item in data.get("products", [])
        }
        instance.employees = {
            item["id"]: Employee.from_dict(item) for item in data.get("employees", [])
        }
        instance.customers = {
            item["id"]: Customer.from_dict(item) for item in data.get("customers", [])
        }
        instance.warehouses = {
            item["id"]: Warehouse.from_dict(item)
            for item in data.get("warehouses", [])
        }
        instance.sales_points = {
            item["id"]: SalesPoint.from_dict(item)
            for item in data.get("sales_points", [])
        }
        instance.orders = [Order.from_dict(item) for item in data.get("orders", [])]
        instance.next_ids.update(data.get("next_ids", {}))

        return instance


class DataStore:
    """Загрузка и сохранение данных в JSON."""

    def __init__(self, path: Path) -> None:
        self._path = path

    def load(self) -> CRM:
        """Загрузить данные или вернуть пустой CRM."""
        if not self._path.exists():
            return CRM()

        with self._path.open("r", encoding="utf-8") as file:
            data = json.load(file)

        return CRM.from_dict(data)

    def save(self, crm: CRM) -> None:
        """Сохранить данные в JSON."""
        with self._path.open("w", encoding="utf-8") as file:
            json.dump(crm.to_dict(), file, indent=2, ensure_ascii=False)


class CRMApp:
    """Консольный интерфейс и основные действия."""

    def __init__(self, crm: CRM, store: DataStore) -> None:
        self.crm = crm
        self.store = store
        self.actions = {
            "1": ("найм сотрудника", self.action_hire_employee),
            "2": ("увольнение сотрудника", self.action_fire_employee),
            "3": ("добавить покупателя", self.action_add_customer),
            "4": ("добавить товар в каталог", self.action_add_product),
            "5": ("открыть склад", self.action_open_warehouse),
            "6": ("закрыть склад", self.action_close_warehouse),
            "7": ("открыть пункт продаж", self.action_open_sales_point),
            "8": ("закрыть пункт продаж", self.action_close_sales_point),
            "9": ("назначить ответственного", self.action_assign_responsible),
            "10": ("закупка товара", self.action_purchase_product),
            "11": ("перемещение товара", self.action_move_product),
            "12": ("продажа товара", self.action_sell_product),
            "13": ("возврат товара", self.action_return_product),
            "14": ("информация о складе/пункте", self.action_location_info),
            "15": ("информация о запасах", self.action_inventory_info),
            "16": ("информация о товарах", self.action_catalog_info),
            "17": ("доходность", self.action_profit_info),
        }

    def run(self) -> None:
        """Запустить главный цикл меню."""
        print("консольная crm")

        while True:
            self._print_menu()
            choice = input("выберите действие: ").strip()

            if choice == "0":
                self.store.save(self.crm)
                print("выход")
                break

            action = self.actions.get(choice)

            if not action:
                print("неизвестная команда")
                continue

            try:
                action[1]()
                self.store.save(self.crm)
            except ValueError as exc:
                print(f"ошибка: {exc}")

    def _print_menu(self) -> None:
        """Показать меню."""
        print("\n=== crm ===")

        for key in sorted(self.actions, key=lambda x: int(x)):
            print(f"{key}. {self.actions[key][0]}")

        print("0. выход")

    def action_hire_employee(self) -> None:
        """Добавить сотрудника."""
        name = input("имя сотрудника: ").strip()
        phone = input("телефон сотрудника: ").strip()
        position = input("должность сотрудника: ").strip()
        employee_id = self.crm.next_id("employee")
        self.crm.employees[employee_id] = Employee(
            employee_id, name, phone, position
        )
        print(f"сотрудник #{employee_id} добавлен")

    def action_fire_employee(self) -> None:
        """Удалить сотрудника и снять ответственность."""
        employee = self._choose_employee()

        if not employee:
            return

        for warehouse in self.crm.warehouses.values():
            if warehouse.responsible_id == employee.person_id:
                warehouse.responsible_id = None

        for sales_point in self.crm.sales_points.values():
            if sales_point.responsible_id == employee.person_id:
                sales_point.responsible_id = None

        self.crm.employees.pop(employee.person_id, None)
        print("сотрудник удален")

    def action_add_customer(self) -> None:
        """Добавить покупателя."""
        name = input("имя покупателя: ").strip()
        phone = input("телефон покупателя: ").strip()
        customer_id = self.crm.next_id("customer")
        self.crm.customers[customer_id] = Customer(customer_id, name, phone)
        print(f"покупатель #{customer_id} добавлен")

    def action_add_product(self) -> None:
        """Добавить товар в каталог."""
        name = input("название товара: ").strip()
        purchase_price = _prompt_float("закупочная цена: ")
        sale_price = _prompt_float("цена продажи: ")
        product_id = self.crm.next_id("product")
        self.crm.products[product_id] = Product(
            product_id, name, purchase_price, sale_price
        )
        print(f"товар #{product_id} добавлен")

    def action_open_warehouse(self) -> None:
        """Открыть склад и создать ячейки."""
        name = input("название склада: ").strip()
        cells_count = _prompt_int("количество ячеек: ", min_value=1)
        capacity = _prompt_int("вместимость ячейки: ", min_value=1)
        warehouse_id = self.crm.next_id("warehouse")
        warehouse = Warehouse(warehouse_id, name, None)

        for _ in range(cells_count):
            warehouse.add_cell(capacity)

        self.crm.warehouses[warehouse_id] = warehouse
        print(f"склад #{warehouse_id} открыт")

    def action_close_warehouse(self) -> None:
        """Закрыть склад, если он пуст."""
        warehouse = self._choose_warehouse()

        if not warehouse:
            return

        if warehouse.inventory_items():
            print("склад не пуст")
            return

        self.crm.warehouses.pop(warehouse.location_id, None)
        print("склад закрыт")

    def action_open_sales_point(self) -> None:
        """Открыть пункт продаж."""
        name = input("название пункта продаж: ").strip()
        sales_id = self.crm.next_id("sales_point")
        self.crm.sales_points[sales_id] = SalesPoint(sales_id, name, None)
        print(f"пункт продаж #{sales_id} открыт")

    def action_close_sales_point(self) -> None:
        """Закрыть пункт продаж, если он пуст."""
        sales_point = self._choose_sales_point()

        if not sales_point:
            return

        if sales_point.inventory_items():
            print("пункт продаж не пуст")
            return

        self.crm.sales_points.pop(sales_point.location_id, None)
        print("пункт продаж закрыт")

    def action_assign_responsible(self) -> None:
        """Назначить ответственного сотрудника."""
        location = self._choose_location()

        if not location:
            return

        employee = self._choose_employee()

        if not employee:
            return

        location.responsible_id = employee.person_id
        print("ответственный обновлен")

    def action_purchase_product(self) -> None:
        """Закупка товара на склад."""
        warehouse = self._choose_warehouse()

        if not warehouse:
            return

        cell = self._choose_cell(warehouse)

        if not cell:
            return

        product = self._choose_product()

        if not product:
            return

        quantity = _prompt_int("количество: ", min_value=1)
        warehouse.add_stock(product.product_id, quantity, cell.cell_id)
        amount = -product.purchase_price * quantity
        order = self._create_order(
            kind="закупка",
            product_id=product.product_id,
            quantity=quantity,
            unit_price=product.purchase_price,
            amount=amount,
            warehouse_id=warehouse.location_id,
            sales_point_id=None,
            customer_id=None,
        )
        self.crm.orders.append(order)
        print("закупка сохранена")

    def action_move_product(self) -> None:
        """Перемещение товара между объектами."""
        source = self._choose_location(prompt="источник (1-склад, 2-пункт): ")

        if not source:
            return

        source_cell = (
            self._choose_cell(source) if isinstance(source, Warehouse) else None
        )
        product = self._choose_product()

        if not product:
            return

        quantity = _prompt_int("количество: ", min_value=1)
        dest = self._choose_location(prompt="назначение (1-склад, 2-пункт): ")

        if not dest:
            return

        dest_cell = (
            self._choose_cell(dest) if isinstance(dest, Warehouse) else None
        )
        source.remove_stock(
            product.product_id,
            quantity,
            _cell_id(source_cell),
        )
        dest.add_stock(
            product.product_id,
            quantity,
            _cell_id(dest_cell),
        )
        print("перемещение выполнено")

    def action_sell_product(self) -> None:
        """Продажа товара из пункта продаж."""
        sales_point = self._choose_sales_point()

        if not sales_point:
            return

        product = self._choose_product()

        if not product:
            return

        quantity = _prompt_int("количество: ", min_value=1)
        customer = self._choose_customer(optional=True)
        customer_id = customer.person_id if customer else None
        sales_point.remove_stock(product.product_id, quantity)
        amount = product.sale_price * quantity
        order = self._create_order(
            kind="продажа",
            product_id=product.product_id,
            quantity=quantity,
            unit_price=product.sale_price,
            amount=amount,
            warehouse_id=None,
            sales_point_id=sales_point.location_id,
            customer_id=customer_id,
        )
        self.crm.orders.append(order)
        print("продажа сохранена")

    def action_return_product(self) -> None:
        """Возврат товара в пункт продаж."""
        sales_point = self._choose_sales_point()

        if not sales_point:
            return

        product = self._choose_product()

        if not product:
            return

        quantity = _prompt_int("количество: ", min_value=1)
        sales_point.add_stock(product.product_id, quantity)
        amount = -product.sale_price * quantity
        order = self._create_order(
            kind="возврат",
            product_id=product.product_id,
            quantity=quantity,
            unit_price=product.sale_price,
            amount=amount,
            warehouse_id=None,
            sales_point_id=sales_point.location_id,
            customer_id=None,
        )
        self.crm.orders.append(order)
        print("возврат сохранен")

    def action_location_info(self) -> None:
        """Показать информацию о складе или пункте продаж."""
        location = self._choose_location()
        if not location:
            return

        print(location.summary())
        responsible = self.crm.employees.get(location.responsible_id)

        if responsible:
            print(f"ответственный: {responsible.name}")
        else:
            print("ответственный: не назначен")

        if isinstance(location, Warehouse):
            print("ячейки")

            for cell in location.cells().values():
                print(
                    f"- ячейка {cell.cell_id}: "
                    f"занято {cell.used_capacity()}/{cell.capacity}"
                )

    def action_inventory_info(self) -> None:
        """Показать запасы на складе или в пункте продаж."""
        location = self._choose_location()

        if not location:
            return

        items = location.inventory_items()

        if not items:
            print("запасы пусты")
            return

        self._print_inventory(items)

    def action_catalog_info(self) -> None:
        """Показать список товаров, доступных к закупке."""
        if not self.crm.products:
            print("каталог пуст")
            return

        print("каталог")

        for product in self.crm.products.values():
            print(
                f"#{product.product_id} {product.name} "
                f"(закупка {product.purchase_price:.2f}, "
                f"продажа {product.sale_price:.2f})"
            )

    def action_profit_info(self) -> None:
        """Показать доходность предприятия и пунктов продаж."""
        total = sum(order.amount for order in self.crm.orders)
        print(f"общая прибыль: {total:.2f}")

        if not self.crm.sales_points:
            return

        print("пункты продаж")

        for sales_point in self.crm.sales_points.values():
            amount = sum(
                order.amount
                for order in self.crm.orders
                if order.sales_point_id == sales_point.location_id
            )
            print(f"- {sales_point.name}: {amount:.2f}")

    def _create_order(
        self,
        kind: str,
        product_id: int,
        quantity: int,
        unit_price: float,
        amount: float,
        warehouse_id: Optional[int],
        sales_point_id: Optional[int],
        customer_id: Optional[int],
    ) -> Order:
        """Создать заказ с новым id."""
        order_id = self.crm.next_id("order")

        return Order(
            order_id=order_id,
            kind=kind,
            product_id=product_id,
            quantity=quantity,
            unit_price=unit_price,
            amount=amount,
            warehouse_id=warehouse_id,
            sales_point_id=sales_point_id,
            customer_id=customer_id,
            created_at=datetime.now().isoformat(timespec="seconds"),
        )

    def _choose_employee(self) -> Optional[Employee]:
        """Выбрать сотрудника."""
        if not self.crm.employees:
            print("сотрудников нет")
            return None

        print("сотрудники")

        for employee in self.crm.employees.values():
            print(f"#{employee.person_id}: {employee.name} ({employee.position})")

        employee_id = _prompt_int("id сотрудника: ")

        return self.crm.employees.get(employee_id)

    def _choose_customer(self, optional: bool = False) -> Optional[Customer]:
        """Выбрать покупателя."""
        if not self.crm.customers:
            if optional:
                return None
            print("покупателей нет")
            return None

        print("покупатели")

        for customer in self.crm.customers.values():
            print(f"#{customer.person_id}: {customer.name}")

        if optional:
            raw = input("id покупателя (пусто - пропуск): ").strip()
            if not raw:
                return None
            customer_id = int(raw)
        else:
            customer_id = _prompt_int("id покупателя: ")

        return self.crm.customers.get(customer_id)

    def _choose_product(self) -> Optional[Product]:
        """Выбрать товар."""
        if not self.crm.products:
            print("каталог пуст")
            return None

        print("товары")

        for product in self.crm.products.values():
            print(f"#{product.product_id}: {product.name}")

        product_id = _prompt_int("id товара: ")

        return self.crm.products.get(product_id)

    def _choose_warehouse(self) -> Optional[Warehouse]:
        """Выбрать склад."""
        if not self.crm.warehouses:
            print("складов нет")
            return None

        print("склады")

        for warehouse in self.crm.warehouses.values():
            print(f"#{warehouse.location_id}: {warehouse.name}")

        warehouse_id = _prompt_int("id склада: ")

        return self.crm.warehouses.get(warehouse_id)

    def _choose_sales_point(self) -> Optional[SalesPoint]:
        """Выбрать пункт продаж."""
        if not self.crm.sales_points:
            print("пунктов продаж нет")
            return None

        print("пункты продаж")

        for sales_point in self.crm.sales_points.values():
            print(f"#{sales_point.location_id}: {sales_point.name}")

        sales_id = _prompt_int("id пункта продаж: ")

        return self.crm.sales_points.get(sales_id)

    def _choose_cell(self, warehouse: Warehouse) -> Optional[WarehouseCell]:
        """Выбрать ячейку склада."""
        cells = warehouse.cells()
        if not cells:
            print("ячеек на складе нет")
            return None

        print("ячейки")

        for cell in cells.values():
            print(f"{cell.cell_id} (свободно {cell.available_capacity()})")

        cell_id = _prompt_int("id ячейки: ")

        return cells.get(cell_id)

    def _choose_location(
        self,
        prompt: str = "тип объекта (1-склад, 2-пункт): ",
    ) -> Optional[StorageLocation]:
        """Выбрать склад или пункт продаж."""
        loc_type = input(prompt).strip()

        if loc_type == "1":
            return self._choose_warehouse()

        if loc_type == "2":
            return self._choose_sales_point()

        print("неизвестный тип объекта")
        return None

    def _print_inventory(self, items: Dict[int, int]) -> None:
        """Показать список запасов с названиями товаров."""
        print("запасы")

        for product_id, qty in sorted(items.items()):
            product = self.crm.products.get(product_id)
            name = product.name if product else "неизвестно"
            print(f"- #{product_id} {name}: {qty}")


def _prompt_int(label: str, min_value: Optional[int] = None) -> int:
    """Запросить целое число у пользователя."""
    while True:
        raw = input(label).strip()

        try:
            value = int(raw)
        except ValueError:
            print("введите целое число")
            continue

        if min_value is not None and value < min_value:
            print(f"значение должно быть >= {min_value}")
            continue

        return value


def _prompt_float(label: str) -> float:
    """Запросить число у пользователя."""
    while True:
        raw = input(label).strip()

        try:
            return float(raw)
        except ValueError:
            print("введите число")


def _int_dict_to_json(data: Dict[int, int]) -> Dict[str, int]:
    """Преобразовать словарь с int ключами для JSON."""
    return {str(key): value for key, value in data.items()}


def _json_dict_to_int(data: Dict[str, int]) -> Dict[int, int]:
    """Преобразовать словарь JSON в int ключи."""
    return {int(key): int(value) for key, value in data.items()}


def _optional_int(value: Optional[int]) -> Optional[int]:
    """Вернуть int или None."""
    if value is None:
        return None
    return int(value)


def _cell_id(cell: Optional[WarehouseCell]) -> Optional[int]:
    """Вернуть id ячейки или None."""
    return cell.cell_id if cell else None


def main() -> None:
    """Точка входа."""
    data_path = Path(__file__).resolve().with_name(DATA_FILE_NAME)
    store = DataStore(data_path)
    app = CRMApp(store.load(), store)

    app.run()


if __name__ == "__main__":
    main()