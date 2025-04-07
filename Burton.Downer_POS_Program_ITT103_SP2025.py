import uuid #used to generate order ID on sales receipt
from datetime import datetime #generate current date on sales receipt
import time #used to delay program exit for 3 seconds
from collections import defaultdict #used to group products by category in inventory

#\\USER & PRODUCT CLASSES
#product class to handle product ID, name, price, stock and category
#product ID is unique to each product
#user class to handle username, password and role
class Product:
    def __init__(self, product_id, name, price, stock, category='General, Groceries, Household, Electronics'):
        self.id = product_id
        self.name = name
        self.price = price
        self.stock = stock
        self.category = category

    def __str__(self):
        return f"{self.id}. {self.name}   ${self.price:.2f} || Stock: {self.stock} | Category: {self.category}"
        
    def to_dict(self): #function to convert product object to dictionary for JSON serialization
        return {
            'id': self.id,
            'name': self.name,
            'price': self.price,
            'stock': self.stock,
            'category': self.category
        }

class User:
    def __init__(self, username, password, role="cashier"):
        self.username = username
        self.password = password
        self.role = role

    def has_permission(self, required_role): #function to check if user has permission to perform certain actions
        return self.role == required_role

    def to_dict(self): #function to convert user object to dictionary for JSON serialization
        return {
            'username': self.user,
            'password': self.pwd,
            'role': self.cashier,
            'permissions': self.role
        }

#\\DISCOUNT CLASS
#handles discount rate for the POS system
#discount rate is set to 5% for all products once threshold is met
class Discount:
    def apply_discount(self, subtotal):
        return subtotal * 0.05 #5% discount on subtotal

#\\CART & CART ITEM CLASSES
#handles products added to cart after it is selected
#ensures that the quantity is a positive integer
#and that the product is available in stock
class CartItem:
    def __init__(self, product, quantity): #initializes cart item with product and quantity
        if not isinstance(quantity, int) or quantity <= 0:
            raise ValueError("Quantity must be a positive value.")
        self.product = product
        self.quantity = quantity

    def total_price(self): #calculates total price of the product in the cart
        return self.product.price * self.quantity

#manages shopping cart for selected items customer intends to buy
#ensures that the cart is empty before adding items
class Cart:
    def __init__(self): #initializes cart with empty list
        self.items = []
        self.discount = Discount()

    def clear(self): #clears cart
        self.items = []

    def add_item(self, product, quantity): #adds a product to the cart with a specified quantity
        if not isinstance(quantity, int) or quantity <= 0:
            print("Quantity must be a positive value.\n")
            return False

        #check if product already exists in cart
        #if it does, update the quantity and check stock
        for item in self.items:
            if item.product.id == product.id:
                total_quantity = item.quantity + quantity
                if total_quantity > product.stock: #ensures the selected quantity is not more than the stock available
                    print(f"Insufficient stock for {product.name}. Only {product.stock - item.quantity} additional can be added.\n")
                    return False
                item.quantity += quantity #updates quantity of product in cart
                self.check_low_stock(item.product)
                product.stock -= quantity #updates stock of product in inventory
                self.check_low_stock(product)
                return True

        if quantity > product.stock: #checks if requested quantity is more than stock in inventory
            print(f"Insufficient stock for {product.name}. Only {product.stock} available.\n")
            return False

        cart_item = CartItem(product, quantity)
        self.items.append(cart_item) #appends item to the cart for same item already in cart
        product.stock -= quantity #updates stock of product in inventory
        self.check_low_stock(product)
        return True

    def check_low_stock(self, product):
        if product.stock <= 5: #alerts cashier of low stock once threshold is reached
            print(f"⚠️ Low Stock Alert: {product.name} only has {product.stock} left! ⚠️\n")

    #removes a specified quantity of a product from the cart
    #ensures cart is not empty and that the selected item is present in the cart
    def remove_item(self, product_id, quantity):
        removed = False
        for item in list(self.items):
            if item.product.id == product_id:
                if quantity > item.quantity: #checks if requested quantity is more than quantity in cart
                    print(f"\nCannot remove {quantity} units. Only {item.quantity} {item.product.name}(s) in cart.\n")
                    print("NO CHANGES MADE\n")
                    return False
                item.product.stock += quantity #updates stock of product in inventory
                self.check_low_stock(item.product)
                item.quantity -= quantity #updates quantity of product in cart
                if item.quantity == 0:
                    self.items.remove(item) 
                print(f"Removed {quantity} x {item.product.name}. Cart quantity now {item.quantity}.\n")
                print(f"Product stock updated to: {item.product.stock}.\n")
                self.check_low_stock(item.product)
                removed = True
        if not removed:
            print("Item not found. No changes made.\n")
            return False
        return True

    def get_all_items(self): #returns all items in the cart
        return [(item.product, item.quantity) for item in self.items]

    def is_empty(self): #checks if cart is empty
        return not self.items

    def calculate_subtotal(self): #calculates subtotal of all items in the cart
        return sum(item.total_price() for item in self.items)

    def apply_discount(self, discount): #applies discount rate to the subtotal
        self.discount = discount
    #calculates discount amount based on subtotal in accordance with the discount rate
    def discount_amount(self, subtotal):
        return self.discount.apply_discount(subtotal) if subtotal >= 5000 else self.discount == 0
    
    #function to display cart items and calculate subtotal, tax, discount & total
    def display_receipt(self, tax_rate):
        print()
        print("------ Current Cart Items ------".center(40))
        print()
        for item in self.items: #displays items in cart
            print(f"{item.quantity} x {item.product.name} @ ${item.product.price:,.2f}   ${item.total_price():,.2f}\n")
        subtotal = self.calculate_subtotal()
        tax = subtotal * tax_rate
        discount = self.discount_amount(subtotal)
        total = (subtotal + tax) - discount

        print(f"{'Subtotal:':<35} ${subtotal:,.2f}")
        print(f"{f'Tax ({tax_rate * 100:.0f}%):':<35} ${tax:,.2f}")
        if discount > 0:
                print(f"{f'Discount:':<35}-${discount:,.2f}")
        print(f"{'Total Payment Due: ':<35} ${total:,.2f}\n")
        return total

#\\MAIN POS SYSTEM
#POS class controls the main functionality of POS system
#cashier can add or remove items from cart, view cart, checkout and view inventory
#payment and receipt generation
class POS:
    def __init__(self, tax_rate=0.10, store_name="Best Buy Retail Store",
                 store_address="7 Magic Way, Mullah District, Richmond"):
        self.store_name = store_name
        self.store_address = store_address 
        self.tax_rate = tax_rate
        self.users = self._initialize_users()
        self.current_user = None
        self.inventory = self._initialize_inventory()
        self.cart = Cart()
        self.telephone = "1-658-619-9000" #store telephone number

    def _initialize_users(self): #function to initialize users with username, password and role
        return {
            'admin': User('admin', 'admin123', 'admin'),
            'manager': User('manager', 'mgr123', 'admin'),
            'adowner': User('adowner', 'moneyo'),
            'dburton': User('dburton', 'chiching')
        }

    def _initialize_inventory(self): #function to initialize inventory with products, price and stock available
        products = {

            40: Product(40, "Notebook", 500.00, 8, "General"),
            45: Product(45, "Unmaster Lock Padlock", 400.00, 5, "General"),
            101: Product(101, "Rice (5lb)", 480.00, 25, "Groceries"),
            102: Product(102, "Flour (5lb)", 430.00, 28, "Groceries"),
            103: Product(103, "Bread", 600.00, 30, "Groceries"),
            104: Product(104, "Milk", 770.00, 15, "Groceries"),
            105: Product(105, "Eggs (dozen)", 780.00, 20, "Groceries"),
            106: Product(106, "Sugar (5lb)", 400.00, 25, "Groceries"),
            107: Product(107, "Pasta", 120.00, 30, "Groceries"),
            108: Product(108, "Butter", 250.00, 20, "Groceries"),
            109: Product(109, "Canned Beans (1kg)", 320.00, 10, "Groceries"),
            110: Product(110, "Honey", 1940.00, 8, "Groceries"),
            201: Product(201, "Laundry Detergent", 1050.00, 14, "Household"),
            202: Product(202, "Bleach", 250.00, 16, "Household"),
            203: Product(203, "Tissue", 160.00, 36, "Household"),
            204: Product(204, "Olive Oil (1L)", 165.00, 24, "Household"),
            205: Product(205, "Dishwashing Liquid", 175.00, 16, "Household"),
            206: Product(206, "Coconut Oil (1L)", 910.00, 8, "Household"),
            207: Product(207, "Desk Fan", 8500.00, 12, "Household"),
            208: Product(208, "Frying Pan (med)", 5560.00, 6, "Household"),
            209: Product(209, "Light Bulb", 700.00, 18, "Household"),
            210: Product(210, "Fabric Softener", 300.00, 10, "Household"),
            211: Product(211, "Toothbrush", 630.00, 12, "Household"),
            212: Product(212, "Broom", 600.00, 15, "Household"),
            213: Product(213, "Foil Paper", 660.00, 30, "Household"),
            214: Product(214, "Rum (750ml)", 1700.00, 24, "Household"),
            215: Product(215, "Baking Powder (500g)", 140.00, 16, "Household"),
            301: Product(301, "Wireless Mouse", 1550, 11, "Electronics"),
            302: Product(302, "Bluetooth Buds", 3100.00, 7, "Electronics"),
            303: Product(303, "Apple iPad Pro", 35000.00, 6, "Electronics"),
            304: Product(304, "Smart Speaker", 4500.00, 11, "Electronics"),
            305: Product(305, "USB-C Cable", 2000.00, 20, "Electronics"),
        }
        return products

    #\\USER AUTHENTICATION
    def login(self): #function to handle user login with an attempt limit of 3
        attempts = 3 #maximum number of login attempts
        while attempts > 0: #loop until user is logged in or attempts are exhausted
            print("\n" + "=" * 25)
            print("LOGIN".center(25))
            print("=" * 25)
            username = input("Username: ").strip()
            password = input("Password: ").strip()
            
            user = self.users.get(username) #fetch user from the dictionary
            if user and user.password == password:
                self.current_user = user
                print(f"\nWelcome, {user.username}!")
                return True
            
            attempts -= 1 #decrement attempts if login fails
            print(f"Invalid credentials. {attempts} attempts remaining.")
            if attempts == 0: #if attempts are exhausted, exit the program
                print("Login attempts exceeded! Please relaunch application.")
                time.sleep(3) #program closes gracefully after 3 seconds delay
                return False
    
    def admin_login(self): #function to handle admin login
            print("\n" + "=" * 25)
            print("ADMIN LOGIN".center(25))
            print("=" * 25)
            username = input("Admin Username: ").strip()
            password = input("Admin Password: ").strip()
        
            user = self.users.get(username) #fetch user from the dictionary
            if user and user.password == password and (user.has_permission('admin')):
                self.current_user = user
                print(f"\nAdmin {user.username} logged in.")
                return True
        
            print("\nAdmin login failed. Please retry.\n")
            time.sleep(2) #time delay before input prompt is displayed again
            return False

    #\\PRODUCT SEARCH
    def search_products(self, query): #search for products in the inventory by name or category
        results = []
        query = query.lower() #convert query to lowercase for case-insensitive search
        for product in self.inventory.values():
            if (query in product.name.lower()) or (query in product.category.lower()):
                results.append(product)
        return results

    #\\CORE POS
    def show_inventory(self): #function to display inventory
        print("\n       === Current Inventory ===")
        #group products by first digit of ID
        categories = defaultdict(list)
        for product in self.inventory.values():
            category = str(product.id)[0]
            categories[category].append(product)
        
        for category, products in sorted(categories.items()):
            print(f"\nCategory {category} Items:")
            for product in products:
                print(f"  {product}")
        print("*" * 55 )

    def main_menu(self): #interactive menu options to navigate the POS system
        print("\n" + "=" * 30)
        print("PayPoint POS Menu".center(30))
        print("=" * 30)
        print("1. New Transaction")
        print("2. View Cart")
        print("3. Checkout")
        print("4. View Inventory")
        print("5. Logout")
        print("6. Exit")
        print("=" * 30)
    
    #\\NEW TRANSACTION
    #function to handle new transactions under a dedicated menu
    #cashier can add or remove items from cart, view cart, checkout and cancel transaction
    def new_sale(self):
        self.cart = Cart()
        while True:
            print("\n=== New Transaction ===")
            print("1. Add Item(s)")
            print("2. Remove Item(s)")
            print("3. View Cart")
            print("4. Checkout")
            print("5. Cancel Transaction")
            
            choice = input("\nSelect an option: ").strip() #prompts cashier for menu choice
            
            if choice == '1':
                self.add_item_to_cart()
            elif choice == '2':
                if self.current_user.has_permission('admin'):
                   self.remove_item_fr_cart()
                else:
                    print("Access denied. Admin privileges required.")
            elif choice == '3':
                self.view_cart()
            elif choice == '4':
                if self.checkout():
                    return
            elif choice == '5':
                if input("Confirm cancelled transaction? (yes/no): ").lower() == 'yes':
                    self.cancel_sale()
                    return
            else:
                print("Invalid choice. Try again.")

    def add_item_to_cart(self): #add item to cart during new transaction
        search_query = input("Search product by name/category (or leave blank to view all): ").strip()
        if search_query:
            results = self.search_products(search_query)
            if not results: 
                print("No matching products found.")
                return
            print("\n=== Search Results ===")
            for product in results:
                print(product)
        else:
            self.show_inventory()
            time.sleep(1.5) #time delay before input prompt is displayed again
        
        try:
            product_id = int(input("\nEnter Product ID: "))
            product = self.inventory.get(product_id)
            if not product:
                print("Product not found.")
                return
            
            quantity = int(input(f"Enter quantity for {product.name} (Stock: {product.stock}): "))
            if quantity <= 0:
                print("Quantity must be at least 1.")
                return
            
            if self.cart.add_item(product, quantity):
                print(f"Added {quantity} {product.name}(s) to cart.")
            
        except ValueError:
            print("Invalid input. Please enter numbers only.")

    def remove_item_fr_cart(self): #remove item from cart during new transaction
        if self.cart.is_empty(): #check if cart is empty
            print("Cart is empty.\n")
            return False

        search_query = input("Search item in cart by name/category (or leave blank to view all): ").strip()
        cart_items = self.cart.get_all_items() #get all items in cart item quantity, product ID and name

        if search_query:
            results = [
                (product, qty) for product, qty in cart_items
                if search_query.lower() in product.name.lower() or search_query.lower() in product.category.lower()
            ]
            if not results:
                print("No matching items found in cart.")
                return False
            print("\n=== Matching Cart Items ===")
            for product, qty in results:
                print(f"{product} | Quantity in cart: {qty}")
        else:
            print("\n=== Cart Contents ===")
            for product, qty in cart_items:
                print(f"{product} | Quantity in cart: {qty}")

        try:
            product_id = int(input("Enter Product ID to remove: "))
            quantity = int(input("Enter quantity to remove: "))
            success = self.cart.remove_item(product_id, quantity)
            if success:
                if self.cart.is_empty():
                    print("Cart is now empty. Returning to menu...\n")
                    time.sleep(2)
                    self.new_sale()
                else:
                    subtotal = self.cart.calculate_subtotal()
                    tax = subtotal * self.tax_rate
                    discount = self.cart.discount_amount(subtotal)
                    total = (subtotal + tax) - discount
                    subtotal, tax, discount, total = self.recalculate_total()
                    print(f"Updated Cart Total: ${total:,.2f}")
                    time.sleep(1.5)
                return True  # Return True when removal is successful
            return False  # Return False when removal fails
        except ValueError:
            print("Invalid input. Please enter numbers only.")
            return

    def view_cart(self): #display cart if loaded
        if self.cart.is_empty():
            print("Cart is empty.\n")
        else:
            self.cart.display_receipt(self.tax_rate)
    
    def cancel_sale(self): #function to cancel transaction & handle restocking
        for item in self.cart.items:
            item.product.stock += item.quantity #restock item
        self.cart.clear() #clear cart
        print("Transaction cancelled. Inventory restored.")
        time.sleep(2) #time delay before main menu is displayed again
    
    def recalculate_total(self): #recalculate totals after item removal during checkout
        subtotal = self.cart.calculate_subtotal()
        tax = subtotal * self.tax_rate
        discount = self.cart.discount_amount(subtotal)
        total = (subtotal + tax) - discount
        return subtotal, tax, discount, total

    #\\CHECKOUT
    #function to handle checkout process
    #ensures that the cart is not empty before proceeding to checkout
    #calculates subtotal, tax, discount & total
    #handles payment and generates receipt
    def checkout(self): #function to handle checkout process
        if self.cart.is_empty():
            print("Cart is empty. Add item(s) before you can checkout.\n")
            return False
        #cart contents are shown and subtotal, tax, discount & total are calculated
        #payment summary is provided giving cashier prelim calculations
        while True:
            self.view_cart()
            subtotal = self.cart.calculate_subtotal()
            tax = subtotal * self.tax_rate
            discount = self.cart.discount_amount(subtotal)
            total = (subtotal + tax) - discount

            print("====== Payment Summary ======".center(40))
            print(f"{'Subtotal:':<35} ${subtotal:,.2f}")
            print(f"{f'Tax ({self.tax_rate*100:.0f}%):':<35} ${tax:,.2f}")
            if discount > 0:
                print(f"{f'Discount:':<35}-${discount:,.2f}")
            print(f"{'TOTAL DUE:':<35} ${total:,.2f}")

            try: #prompt cashier for payment amount
                payment = float(input(f"\nTotal Due: ${total:,.2f}\nEnter payment amount: $"))
                if payment < total: #check if payment is less than total due
                    shortfall = total - payment
                    print(f"\nInsufficient payment. You need ${shortfall:,.2f} more.\n")
                    #prompt cashier for options to add more funds, remove items or cancel checkout
                    while True:
                        choice = input("Would you like to:\n1. Add more funds\n2. Remove items\n3. Cancel checkout\n\nEnter option here: ")
                    
                        if choice == '1':
                            break #continue to payment entry
                        elif choice == '2':
                            removed = False
                            if not self.current_user.has_permission('admin'):
                                print("\nAdmin privileges required to remove items during checkout.")
                                print("Please call a supervisor or add more funds.")
                                if input("\nSwitch to admin? (yes/no): ").lower() in ['yes', 'y']:
                                    original_user = self.current_user
                                    if self.admin_login():
                                        removed = self.remove_item_fr_cart()
                                        self.current_user = original_user
                                        if removed:
                                            break #continue to payment entry
                                    else: #if admin login fails return to options to choose again
                                        continue
                                else: #if user chooses not to switch to admin return to payment entry without changes
                                    print("Returning to payment options...\n")
                                    continue
                            else: #if user has admin privileges
                                removed = self.remove_item_fr_cart()
                                if removed: #if item removal is successful
                                    break #continue to payment entry
                                else: #if item removal fails
                                    print("No items removed. Returning to payment entry...\n")
                                    return False
                        elif choice == '3': #cancel checkout & confirm
                            if input("\nConfirm transaction cancellation (yes/no): ").lower() in ['yes', 'y']:
                                self.cancel_sale() #cancel transaction
                                return True
                            else: #if user chooses not to cancel transaction
                                print("\nCheckout cancellation aborted.")
                                return False
                        else: #handle invalid input for choice
                            print("\nInvalid choice. Please try again.")
                            return False
                else: #process payment if amount is sufficient
                    change = payment - total #calculate change
                    self.print_receipt(subtotal, tax, discount, total, payment, change)
                    return True
            except ValueError: #handle invalid input for payment amount
                    print("Invalid amount. Enter a valid number.\n")
    
    #\\RECEIPT GENERATION
    #function to generate receipt after payment is made
    #receipt includes order ID, date, cashier name, purchased items, amount paid, subtotal, 
    #tax, discount, total due and change
    def print_receipt(self, subtotal, tax, discount, total, payment, change):
        #generate unique order ID using current date and time
        order_id = datetime.now().strftime("%Y%m%d%H%M%S") + "_" + uuid.uuid4().hex[:5]
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M :%S") #fetch current date and time
        cashier = self.current_user.username #fetch cashier username who processed the order

        print("\n" + "=" * 45) #receipt header
        print(f"{self.store_name.center(40)}")
        print(f"{self.store_address.center(40)}")
        print(f"{self.telephone.center(40)}")
        print("=" * 45)
        print(f"Order ID: {order_id}")
        print(f"Date: {timestamp}")
        print(f"{'\nCashier:':<10}{cashier}")
        print("\n" + "-" * 45)
        
        for item in self.cart.items: #display purchased items
            print(f"{item.quantity} @ ${item.product.price:,.2f} {item.product.name.ljust(20)} ${item.total_price():<7,.2f}")
        
        print("\n" + "-" * 45) #receipt footer
        print(f"Subtotal: ${subtotal:,.2f}")
        print(f"Tax ({self.tax_rate * 100:.0f}%): ${tax:,.2f}")
        if discount > 0:
            print(f"Discount: -${discount:,.2f}")
        print(f"Amount Paid: ${payment:,.2f}")
        print(f"Change: ${change:,.2f}\n")
        print(f"\nTOTAL DUE: ${total:,.2f}")
        print("\n" + "=" * 45) #receipt footer
        print("Thank you for shopping with us!".center(40))
        print("=" * 45 + "\n")
        self.cart.clear()
        time.sleep(2) #time delay before input prompt is displayed again
        return True
        
    #\\MAIN INTERACTION
    #function to run the POS system
    def run(self): #run executable for the POS system
        print(f"\n{self.store_name} PayPoint POS System\n")
        if not self.login(): #prompt for user login if login fails exit the program
            print("Exiting system...")
            time.sleep(3)
            return
        
        while True: #loop to keep the program running until user chooses to exit
            self.cart = Cart() #initialize cart for new transaction
            while True:
                self.main_menu() #display main menu options
                choice = input("\nSelect an option: ").strip() #prompts cashier for menu choice

                if choice == '1': #start new transaction
                    self.new_sale()
                elif choice == '2': #view cart
                    self.view_cart()
                elif choice == '3': #checkout
                    self.checkout()
                elif choice == '4': #view inventory
                    self.show_inventory()
                elif choice == '5':
                    self.current_user = None
                    if not self.login(): #logout user and prompt for login again
                        print("Logged Out.\n")
                        break
                elif choice == '6': #exit the program
                    print("Exiting PayPoint... Goodbye!")
                    time.sleep(3)
                    return
                else:
                    print("Invalid choice. Try again.\n")

if __name__ == "__main__": 
    pos = POS()
    pos.run()
