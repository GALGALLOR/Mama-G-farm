from flask_mysqldb import MySQL
from flask import  get_flashed_messages, session,Flask,render_template,redirect,request,flash,url_for
app=Flask(__name__)
import datetime


mydb=MySQL(app)

"""app.config['MYSQL_HOST']='PharmacyBG.mysql.pythonanywhere-services.com'
app.config['MYSQL_USER']='PharmacyBG'
app.config['MYSQL_PASSWORD']='GALGALLO10'
app.config['MYSQL_DB']='PharmacyBG$default'"""

app.config['MYSQL_HOST']='localhost'
app.config['MYSQL_USER']='root'
app.config['MYSQL_PASSWORD']='GALGALLO10'
app.config['MYSQL_DB']='MAMA_G'

app.secret_key='mimi'

@app.route('/')
def home():
    if 'fullname' in session:
        return redirect(url_for('order'))
    return redirect(url_for('signin'))

@app.route('/sign_in',methods=["GET","POST"])
def signin():
    if request.method=='POST':
        try:
            #check if the user has input something
            fullname = str(request.form["fullname"])
            id_number= int(request.form['id'])
        except:
            #pass if the user submitted blank
            pass
        #check if it is in database
        try:
            
            cursor=mydb.connection.cursor()
            cursor.execute(f'SELECT TWO_NAMES FROM USERS WHERE USER_ID="{id_number}" AND TWO_NAMES="{fullname}" AND ACTIVE="ON"')
            identity=cursor.fetchall()[0][0]
            print(identity)

            #checkin time
            '''checkin_time=datetime.datetime.now().strftime('%H%M00')
            date=datetime.datetime.now().strftime("%Y-%m-%d")
            print(date)

            cursor=mydb.connection.cursor()
            cursor.execute('INSERT INTO WORKLOG(ID_NUMBER,TWO_NAMES,CHECKIN_TIME,DATE)VALUES(%s,%s,%s,%s)',(id_number,fullname,checkin_time,date))
            mydb.connection.commit()'''

            session['fullname']=fullname
            session['id']=id_number

            return redirect(url_for('order'))
        
        except:
            msg = 'the user does not exist'
            print(msg)
            return render_template('signin.html',msg=msg)

        
    else:
        if 'fullname' in session:
            session.pop('fullname', None)
            print("You have been logged out successfully!")
        return render_template('signin.html')

@app.route('/order' ,methods=['POST','GET'] )
def order():
    if 'fullname' in session:
        fullname=session['fullname']
        cursor=mydb.connection.cursor()
        cursor.execute('SELECT * from TRANSACTION WHERE PARTIAL_PAY="YES"')
        partial_pay_data=cursor.fetchall()

        #Get bank Account information
        cursor.execute('SELECT * from ACCOUNT')
        Bank_Account=cursor.fetchall()
        
        if request.method=='POST':
            submit=str(request.form['submit'])
            #PAY OFF DEBT
            if str(submit)=="partial_pay_now":
                Transaction_id = int(request.form['Tid'])
                cursor.execute(f'UPDATE TRANSACTION SET PARTIAL_PAY="NO" WHERE TRANSACTION_ID={Transaction_id}')
                mydb.connection.commit()

                return redirect(url_for('order'))
            #get each itemID and its Quantity bought
            cursor=mydb.connection.cursor()
            cursor.execute('SELECT * from PRODUCTS WHERE STATUS="YES"')
            counter=cursor.fetchall()
            Sold_items=[]
            for num in counter:
                item_='order'+str(num[0])
                sold_item=[]
                sold_item.append(num[0])
                sold_item.append(str(request.form[item_]))
                Sold_items.append(sold_item)
                #stockID,Quantity
            #update sales_table,rem_stock in stock,transaction,transaction_items
            #Ignore if blank
            counter2=0
            for item in Sold_items:
                if int(item[1])>0:
                    counter2=counter2+1
                else:
                    pass
            if counter2 > 0:
                pass
            else:
                return redirect(url_for('order'))
            #Get last Transaction_id
            cursor=mydb.connection.cursor()
            cursor.execute('SELECT TRANSACTION_ID FROM TRANSACTION')
            last_transaction_id=cursor.fetchall()[-1][0]
            last_transaction_id=int(last_transaction_id)+1
            
            
            sale_date=str(datetime.date.today())
            total_cost=0
            #Get stocks_data
            cursor=mydb.connection.cursor()
            cursor.execute('SELECT * FROM STOCK_TABLE')
            last_stocks_data=cursor.fetchall()
            #nanyuki-data
            cursor.execute('SELECT * FROM PRODUCTS WHERE STATUS="YES" ORDER BY PRODUCT_ID DESC')
            products=cursor.fetchall()
            #Get Product cost for each ID
            
            for stockID in Sold_items:
                if int(stockID[1]) == 0:
                    pass
                else:
                    stockID[0]=str(stockID[0])                   
                    cursor=mydb.connection.cursor()
                    cursor.execute('SELECT * FROM PRODUCTS WHERE PRODUCT_ID='+ stockID[0]+' AND STATUS="YES"')
                    cost_product_name=cursor.fetchall()
                    print(' product is ',cost_product_name)
                    cost=cost_product_name[0][3]
                    product_name=str(cost_product_name[0][1])
                    #Get subtotal
                    subtotal=int(cost)*int(stockID[1])
                    total_cost= total_cost + int(subtotal)
                    #Add to Transaction_Items
                    #Get last Transaction_item_id
                    cursor=mydb.connection.cursor()
                    cursor.execute('SELECT TRANSACTION_ITEM_ID FROM TRANSACTION_ITEMS')
                    last_Titem_id=cursor.fetchall()[-1][0]
                    print(last_Titem_id)
                    last_Titem_id=int(last_Titem_id)+1
                    #insert into Transaction_item_id
                    cursor.execute('INSERT INTO TRANSACTION_ITEMS(TRANSACTION_ITEM_ID,TRANSACTION_ID,QUANTITY,UNIT_PRICE,PRODUCT_NAME,SUBTOTAL)VALUES(%s,%s,%s,%s,%s,%s)',(last_Titem_id,last_transaction_id,stockID[1],cost,product_name,subtotal))
                    mydb.connection.commit()
                    #insert into SALES
                    sale_date=datetime.date.today()
                    print(sale_date)
                    

                    

                    #deduct from Inventory in Products
                    rem_stock=int(cost_product_name[0][4])
                    rem_stock=rem_stock-int(stockID[1])
                    cursor.execute(f'UPDATE PRODUCTS SET QUANTITY={rem_stock} WHERE PRODUCT_ID={stockID[0]}')
                    mydb.connection.commit()

            #insert transaction
            if submit=='partial_pay':
                try:
                    customer_name=str(request.form['Customer_name'])
                    amount_paid=str(request.form['Amount_Paid'])
                    amount_rem=int(total_cost)-int(amount_paid)
                    id_number=str(session['id'])
                    cursor.execute('INSERT INTO TRANSACTION(TRANSACTION_ID,CASHIER_ID,SALE_DATE,TOTAL_SALES,PARTIAL_PAY,PARTIAL_PAYER,AMOUNT_REM)VALUES(%s,%s,%s,%s,%s,%s,%s)',(last_transaction_id,id_number,sale_date,total_cost,'YES',customer_name,amount_rem))
                    mydb.connection.commit()
                except:
                    pass

            else:
                id_number=str(session['id'])
                cursor.execute('INSERT INTO TRANSACTION(TRANSACTION_ID,CASHIER_ID,SALE_DATE,TOTAL_SALES,PARTIAL_PAY)VALUES(%s,%s,%s,%s,%s)',(last_transaction_id,id_number,sale_date,total_cost,'NO'))
                mydb.connection.commit()
            #Submit into the account
            #Find CATEGORY
            
            cursor.execute('SELECT * from ACCOUNT ORDER BY BANK_TRANSACTION_ID DESC')
            Bank_Account=cursor.fetchall()
            Bank_balance=int(Bank_Account[0][5])+subtotal
            last_bank_id=int(Bank_Account[0][0])+1
            cursor.execute('INSERT INTO ACCOUNT(BANK_TRANSACTION_ID,TRANSACTION_ID,AMOUNT_IN,BALANCE,DATE,EXPENSE_ID,AMOUNT_OUT,MODE,CATEGORY)VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)',(last_bank_id,last_transaction_id,subtotal,Bank_balance,sale_date,0,0,"TRANSACTION",''))
            mydb.connection.commit()
            
            
            return redirect(url_for('order'))

            
        else:
            pass            
                        

    else:
        return redirect(url_for('signin'))
    
    #list down past transactions
    cursor=mydb.connection.cursor()
    cursor.execute('SELECT * FROM TRANSACTION WHERE PARTIAL_PAY="NO" ORDER BY TRANSACTION_ID DESC ')
    past_transactions=cursor.fetchall()
    cursor.execute('SELECT * FROM TRANSACTION_ITEMS')
    past_transaction_items=cursor.fetchall()
    #list Down products & stock
    cursor.execute('SELECT * FROM PRODUCTS WHERE STATUS="YES" ORDER BY PRODUCT_ID DESC')
    products=cursor.fetchall()
    
    '''cursor.execute('SELECT * FROM STOCK_TABLE')
    stocks=cursor.fetchall()'''
    #set expiry dates
    today=datetime.date.today()
    year=datetime.date.today().year
    month=datetime.date.today().month+4
    date=datetime.date.today().day
    if month>12:
        year=year+1
        month=month-12
    try:
        expiry_range=datetime.date(year,month,date)
    except:
        expiry_range=datetime.date(year,month,25)
    
    user=session['fullname']

    return render_template('order2.html',partial_pay_data=partial_pay_data,products=products, past_transaction_items=past_transaction_items,past_transactions=past_transactions,today=today,user=user)

@app.route('/products' ,methods=['POST','GET'] )
def products():
    if 'fullname' in session:

        #date
        today=datetime.date.today()
        #product details
        cursor=mydb.connection.cursor()
        cursor.execute('SELECT * FROM PRODUCTS ORDER BY STATUS DESC,PRODUCT_ID DESC')
        products=cursor.fetchall()
        cursor.execute('SELECT * FROM PRODUCTS WHERE STATUS="YES" ORDER BY PRODUCT_ID DESC')
        products_active=cursor.fetchall()
        #Finance information
        cursor.execute('SELECT * FROM ACCOUNT ORDER BY BANK_TRANSACTION_ID DESC')
        bank_data=cursor.fetchall()
        if int(bank_data[0][5]) <1000:
            msg='bank balance is low. Top up then Try again'
        else:
            msg=''

        cursor.execute('SELECT * FROM EXPENDITURE ORDER BY EXPENDITURE_ID DESC')
        expenditure=cursor.fetchall()

        #stock data for last stock information
        cursor.execute('SELECT * FROM STOCK_TABLE')
        stockdata=cursor.fetchall()
        cursor.execute('SELECT * FROM STOCK_TABLE ORDER BY STOCK_ID DESC')
        stockdataDesc=cursor.fetchall()
        
        #get staff data
        cursor.execute('SELECT * FROM USERS')
        users=cursor.fetchall()
        #SEE IF MANAGER
        managerCheck="No"
        staffId=session['id']
        cursor.execute(f'SELECT * FROM USERS WHERE USER_ID={staffId}')
        user_details=cursor.fetchall()[0]
        print(user_details)
        if 'anager' in user_details[2]:
            print('MANAGER ALERT')
            managerCheck="Yes"
        elif 'ANAGER' in user_details[2]:
            print('MANAGER ALERT')
            managerCheck="Yes"
        else:
            pass
        #set expiry dates
        year=datetime.date.today().year
        month=datetime.date.today().month+4
        date=datetime.date.today().day
        if month>12:
            year=year+1
            month=month-12
        try:
            expiry_range=datetime.date(year,month,date)
        except:
            expiry_range=datetime.date(year,month,25)

        if request.method=='POST':
            submit=request.form['submit']
            if submit=='restock':
                staffId=session['id']
                productId=request.form['productId']
                productQuantity=int(request.form['Quantity'])
                initial_Q=productQuantity
                
                productBP=request.form['productBP']
                productSP=request.form['productSP']

                try:
                    cursor.execute('SELECT * FROM PRODUCTS WHERE PRODUCT_ID='+str(productId))
                    sources=cursor.fetchall()[0]
                    product_name=sources[1]
                    cursor.execute('SELECT * FROM PRODUCTS WHERE PRODUCT_NAME="'+str(sources[6])+'" AND STATUS="YES" ORDER BY PRODUCT_ID DESC')
                    population1=cursor.fetchall()
                    population=population1[0][4]
                    if 'trays' in product_name:
                        percentage=(30*productQuantity)*100/int(population)
                    elif 'TRAYS' in product_name:
                        percentage=(30*productQuantity)*100/int(population)
                    else:
                        percentage=productQuantity*100/int(population)
                except:
                    population=0
                    percentage=0

                today=datetime.date.today()
                
                #correction 4/8/2023
                #fetch today's restocks
                cursor.execute('SELECT * FROM STOCK_TABLE WHERE STOCK_DATE="'+str(today)+'"')
                stocks_today=cursor.fetchall()
                
                present='no'
                for stock_today in stocks_today:
                    if int(stock_today[1])==int(productId):
                        present='yes'
                        quantity=int(stock_today[3]) + int(productQuantity)
                        
                    else:
                        pass
                print(present)
                #update SellingPrice & Quantity
                for product in products:
                    if int(product[0])==int(productId):
                        category=product[5]
                        NewproductQuantity=int(productQuantity)+int(product[4])
                        
                cursor.execute(f'UPDATE PRODUCTS SET COST={productSP},QUANTITY={NewproductQuantity} WHERE PRODUCT_ID={productId}')
                mydb.connection.commit()
                stock_id=int(stockdataDesc[0][0])+1
                cursor.execute('INSERT INTO STOCK_TABLE(STOCK_ID,PRODUCT_ID,STOCK_DATE,QUANTITY,STAFF_ID,BP,PERCENTAGE)VALUES(%s,%s,%s,%s,%s,%s,%s)',(stock_id,productId,today,productQuantity,staffId,productBP,percentage))
                mydb.connection.commit()
                # Remove money from the account
                subtotal=int(productBP)*int(initial_Q)
                bank_transaction_id=(bank_data[0][0])+1
                bank_balance=(bank_data[0][5])-subtotal
                expenditure_id=int(expenditure[0][0])+1
                if subtotal==0:
                    pass
                else:
                    cashier_id=session['id']
                    cursor.execute('INSERT INTO EXPENDITURE(EXPENDITURE_ID,DATE,COMMODITY_TYPE,COMMODITY_NAME,DESCRIPTION,PROVIDER,QUANTITY,UNIT_PRICE,TRANSPORT_COST,TRANSACTION_COST,SUBTOTAL,CASHIER_ID,STOCK_ID)VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',(expenditure_id,today,'RESTOCK',' ','','',initial_Q,productBP,0,0,subtotal,cashier_id,stock_id))
                    mydb.connection.commit()

                    cursor.execute('INSERT INTO ACCOUNT(BANK_TRANSACTION_ID,EXPENSE_ID,AMOUNT_OUT,BALANCE,DATE,TRANSACTION_ID,AMOUNT_IN,MODE,CATEGORY)VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)',(bank_transaction_id,stock_id,subtotal,bank_balance,today,0,0,"RESTOCK",category))
                    mydb.connection.commit()           
                
                
            
            elif submit=='addNewProduct':
                ProductId=int(products[0][0])+1
                ProductName=request.form['productName']
                Category=request.form['category']
                ProductCost=request.form['productCost']
                productQuantity=0
                source=request.form['source']
                presence='no'

                for product in products:
                    if ProductName==product[1]:
                        if Category==product[5]:
                            if source==product[6]:
                                presence='yes'
                if presence=='no':
                    cursor.execute('INSERT INTO PRODUCTS(PRODUCT_ID,PRODUCT_NAME,CATEGORY,STATUS,COST,QUANTITY,SOURCE)VALUES(%s,%s,%s,%s,%s,%s,%s)',(ProductId,ProductName,Category,'YES',ProductCost,productQuantity,source))
                    mydb.connection.commit()
                    #Update UserLog
                    cursor.execute('SELECT * FROM USER_LOG ORDER BY LOG_ID DESC')
                    last_log_id=int(cursor.fetchall()[0][0])+1
                    
                    cursor.execute('INSERT INTO USER_LOG(LOG_ID,PRODUCT_ID,USER_ID,DATE,ACTIVITY)VALUES(%s,%s,%s,%s,%s)',(last_log_id,ProductId,staffId,today,'ADD'))
                    mydb.connection.commit()
                    
                else:
                    print('The product already exists')
            elif submit=='delete_product':
                productId=request.form['productId']
                print('|The product ID is '+productId)
                cursor.execute('UPDATE PRODUCTS SET STATUS="NO" WHERE PRODUCT_ID='+productId)
                mydb.connection.commit()
                
                #Update UserLog
                cursor.execute('SELECT * FROM USER_LOG ORDER BY LOG_ID DESC')
                
                last_log_id=int(cursor.fetchall()[0][0])+1
                cursor.execute('INSERT INTO USER_LOG(LOG_ID,PRODUCT_ID,USER_ID,DATE,ACTIVITY)VALUES(%s,%s,%s,%s,%s)',(last_log_id,productId,staffId,today,'DELETE'))
                mydb.connection.commit()
            
            elif submit=='activate_product':

                productId=request.form['productId']
                print('|The product ID is '+productId)
                cursor.execute('UPDATE PRODUCTS SET STATUS="YES" WHERE PRODUCT_ID='+productId)
                mydb.connection.commit()
                
                #Update UserLog
                cursor.execute('SELECT * FROM USER_LOG ORDER BY LOG_ID DESC')
                
                last_log_id=int(cursor.fetchall()[0][0])+1
                cursor.execute('INSERT INTO USER_LOG(LOG_ID,PRODUCT_ID,USER_ID,DATE,ACTIVITY)VALUES(%s,%s,%s,%s,%s)',(last_log_id,productId,staffId,today,'ADD'))
                mydb.connection.commit()
                
                
            elif submit=='delete_stock':
                print('delete stock')
                StockId=request.form['StockId']
                print(StockId)
                cursor.execute('DELETE FROM STOCK_TABLE WHERE STOCK_ID='+StockId)
                mydb.connection.commit()
                #Update UserLog
                cursor.execute('SELECT * FROM USER_LOG ORDER BY LOG_ID DESC')
                last_log_id=int(cursor.fetchall()[0][0])+1
                cursor.execute('INSERT INTO USER_LOG(LOG_ID,STOCK_ID,USER_ID,DATE,ACTIVITY)VALUES(%s,%s,%s,%s,%s)',(last_log_id,StockId,staffId,today,'DELETE'))
                mydb.connection.commit()


            elif submit=='NewMember':
                fullname=request.form['FullName']
                IdNumber=request.form['IdNumber']
                contact=request.form['contact']
                title=request.form['title']
                today=datetime.date.today()
                
                cursor.execute('INSERT INTO USERS(USER_ID,TWO_NAMES,TITLE,PHONE_NUMBER,EMPLOYMENT_DATE,ACTIVE)VALUES(%s,%s,%s,%s,%s,%s)',(IdNumber,fullname,title,contact,today,'ON'))
                mydb.connection.commit()
                #Update UserLog
                cursor.execute('SELECT * FROM USER_LOG ORDER BY LOG_ID DESC')
                last_log_id=int(cursor.fetchall()[0][0])+1
                cursor.execute('INSERT INTO USER_LOG(LOG_ID,MEMBER_ID,USER_ID,DATE,ACTIVITY)VALUES(%s,%s,%s,%s,%s)',(last_log_id,IdNumber,staffId,today,'ADD'))
                mydb.connection.commit()
                        
            elif submit=='delete_Member':
                memberId=request.form['memberID']
                cursor.execute('UPDATE USERS SET ACTIVE="OFF" WHERE USER_ID="'+memberId+'"')
                mydb.connection.commit()
                #Update UserLog
                cursor.execute('SELECT * FROM USER_LOG ORDER BY LOG_ID DESC')
                last_log_id=int(cursor.fetchall()[0][0])+1
                cursor.execute('INSERT INTO USER_LOG(LOG_ID,MEMBER_ID,USER_ID,DATE,ACTIVITY)VALUES(%s,%s,%s,%s,%s)',(last_log_id,memberId,staffId,today,'DELETE'))
                mydb.connection.commit()

            elif submit=='ACTIVATE':
                memberId=request.form['memberID']
                cursor.execute('UPDATE USERS SET ACTIVE="ON" WHERE USER_ID="'+memberId+'"')
                mydb.connection.commit()
                #Update UserLog
                cursor.execute('SELECT * FROM USER_LOG ORDER BY LOG_ID DESC')
                last_log_id=int(cursor.fetchall()[0][0])+1
                cursor.execute('INSERT INTO USER_LOG(LOG_ID,MEMBER_ID,USER_ID,DATE,ACTIVITY)VALUES(%s,%s,%s,%s,%s)',(last_log_id,memberId,staffId,today,'ADD'))
                mydb.connection.commit()
            


            return redirect(url_for('products'))

        else:
            pass
    else:
        return redirect(url_for('signin'))
    
    return render_template('products.html',products_active=products_active,msg=msg,today=today,managerCheck=managerCheck,products=products,users=users,stockdata=stockdata,stockdataDesc=stockdataDesc)


@app.route('/accounts' ,methods=['POST','GET'] )
def accounts():
    if 'fullname' in session:
        #user info
        user_id=session['id']
        cursor=mydb.connection.cursor()
        cursor.execute(f'SELECT * FROM USERS WHERE USER_ID={user_id}')
        user=cursor.fetchall()[0]


        cursor.execute(f'SELECT COUNT(*) FROM TRANSACTION WHERE CASHIER_ID={user_id}')
        Products_Sold=cursor.fetchall()[0][0]

        cursor.execute(f'SELECT COUNT(*) FROM STOCK_TABLE WHERE STAFF_ID={user_id}')
        RestocksMade=cursor.fetchall()[0][0]

        cursor.execute(f'SELECT COUNT(*) FROM TRANSACTION WHERE CASHIER_ID={user_id}')
        Products_Sold=cursor.fetchall()[0][0]

        cursor.execute(f'SELECT COUNT(PRODUCT_ID) FROM USER_LOG WHERE USER_ID={user_id} AND ACTIVITY="DELETE" ')
        Products_deleted=cursor.fetchall()[0][0]

        cursor.execute(f'SELECT COUNT(PRODUCT_ID) FROM USER_LOG WHERE USER_ID={user_id} AND ACTIVITY="ADD" ')
        Products_added=cursor.fetchall()[0][0]

        cursor.execute(f'SELECT COUNT(STOCK_ID) FROM USER_LOG WHERE USER_ID={user_id} AND ACTIVITY="DELETE" ')
        stocks_Deleted=cursor.fetchall()[0][0]


        cursor.execute(f'SELECT COUNT(MEMBER_ID) FROM USER_LOG WHERE USER_ID={user_id} AND ACTIVITY="ADD" ')
        members_added=cursor.fetchall()[0][0]

        cursor.execute(f'SELECT COUNT(MEMBER_ID) FROM USER_LOG WHERE USER_ID={user_id} AND ACTIVITY="DELETE" ')
        members_deleted=cursor.fetchall()[0][0]

        cursor.execute(f'SELECT * FROM USERS WHERE TITLE="CASHIER" ')
        cashiers=cursor.fetchall()

    else:
        return redirect(url_for('signin'))
    return render_template('accounts.html',cashiers=cashiers,user=user,members_deleted=members_deleted,members_added=members_added,stocks_Deleted=stocks_Deleted,Products_added=Products_added,Products_deleted=Products_deleted,Products_Sold=Products_Sold,RestocksMade=RestocksMade)

@app.route('/<cashier_id>' ,methods=['POST','GET'] )
def accounts_cashier(cashier_id):
    if 'fullname' in session:
        #user info
        
        user_id=session['id']
        cursor=mydb.connection.cursor()
        cursor.execute(f'SELECT * FROM USERS WHERE USER_ID={cashier_id}')
        user=cursor.fetchall()[0]


        cursor.execute(f'SELECT COUNT(*) FROM TRANSACTION WHERE CASHIER_ID={cashier_id}')
        Products_Sold=cursor.fetchall()[0][0]

        cursor.execute(f'SELECT COUNT(*) FROM STOCK_TABLE WHERE STAFF_ID={cashier_id}')
        RestocksMade=cursor.fetchall()[0][0]

        cursor.execute(f'SELECT COUNT(*) FROM TRANSACTION WHERE CASHIER_ID={cashier_id}')
        Products_Sold=cursor.fetchall()[0][0]

        cursor.execute(f'SELECT COUNT(PRODUCT_ID) FROM USER_LOG WHERE USER_ID={cashier_id} AND ACTIVITY="DELETE" ')
        Products_deleted=cursor.fetchall()[0][0]

        cursor.execute(f'SELECT COUNT(PRODUCT_ID) FROM USER_LOG WHERE USER_ID={cashier_id} AND ACTIVITY="ADD" ')
        Products_added=cursor.fetchall()[0][0]

        cursor.execute(f'SELECT COUNT(STOCK_ID) FROM USER_LOG WHERE USER_ID={cashier_id} AND ACTIVITY="DELETE" ')
        stocks_Deleted=cursor.fetchall()[0][0]


        cursor.execute(f'SELECT COUNT(MEMBER_ID) FROM USER_LOG WHERE USER_ID={cashier_id} AND ACTIVITY="ADD" ')
        members_added=cursor.fetchall()[0][0]

        cursor.execute(f'SELECT COUNT(MEMBER_ID) FROM USER_LOG WHERE USER_ID={cashier_id} AND ACTIVITY="DELETE" ')
        members_deleted=cursor.fetchall()[0][0]

        cursor.execute(f'SELECT * FROM USERS WHERE TITLE="CASHIER" ')
        cashiers=cursor.fetchall()

    else:
        return redirect(url_for('signin'))
    return render_template('cashiers.html',user_id=user_id,cashiers=cashiers,user=user,members_deleted=members_deleted,members_added=members_added,stocks_Deleted=stocks_Deleted,Products_added=Products_added,Products_deleted=Products_deleted,Products_Sold=Products_Sold,RestocksMade=RestocksMade)


@app.route('/store',methods=['GET','POST'])
def store():
    if 'fullname' in session:
        pass
    else:
        return redirect(url_for('signin'))
    cursor=mydb.connection.cursor()
    #Suppliers
    
    #stock_id desc
    cursor.execute('SELECT * FROM STOCK_TABLE ORDER BY STOCK_ID DESC')
    stockdataDesc=cursor.fetchall()
    cursor.execute('SELECT * FROM STOCK_TABLE JOIN PRODUCTS ON PRODUCTS.PRODUCT_ID = STOCK_TABLE.PRODUCT_ID ORDER BY STOCK_DATE DESC,PRODUCT_NAME DESC')
    stockdataDesc1=cursor.fetchall()
    print(stockdataDesc1)
    cursor.execute('SELECT * FROM PRODUCTS ORDER BY STATUS DESC,PRODUCT_ID DESC')
    products=cursor.fetchall()
    
    #set expiry dates
    today=datetime.date.today()
    
    
    return render_template('store.html',stockdataDesc1=stockdataDesc1,today=today,stockdataDesc=stockdataDesc,products=products)

@app.route('/bank',methods=['POST','GET'])
def bank():
    if 'fullname' in session:
        pass
    else:
        return redirect(url_for('signin'))
    cursor = mydb.connection.cursor()
    cursor.execute('SELECT * FROM ACCOUNT ORDER BY BANK_TRANSACTION_ID DESC')
    bank_data=cursor.fetchall()

    cursor.execute('SELECT * FROM EXPENDITURE ORDER BY EXPENDITURE_ID DESC')
    expenditure=cursor.fetchall()
    cursor.execute('SELECT * FROM STOCK_TABLE ORDER BY STOCK_ID DESC')
    stockdata=cursor.fetchall()
    cursor.execute('SELECT * FROM PRODUCTS ORDER BY PRODUCT_ID DESC')
    products=cursor.fetchall()
    cursor.execute('SELECT * FROM TRANSACTION ORDER BY TRANSACTION_ID DESC')
    transactions=cursor.fetchall()
    cursor.execute('SELECT * FROM TRANSACTION_ITEMS ORDER BY TRANSACTION_ITEM_ID DESC')
    transaction_items=cursor.fetchall()
    cursor.execute('SELECT * FROM USERS')
    cashiers=cursor.fetchall()

    available=bank_data[0][5]
    
    if request.method=='POST':
        submit=request.form['submit']
        if submit=='remove':
            commodity_type=request.form['commodity_type']
            commodity_name=request.form['commodity_name']
            description=request.form['description']        
            provider=request.form['provider']
            quantity=request.form['quantity']
            unit_price=request.form['unit_price']
            transaction_cost=request.form['transaction_cost']
            transport_cost=request.form['transport_cost']
            subtotal=(int(quantity)*int(unit_price))+int(transaction_cost)+int(transport_cost)
            expenditure_id=int(expenditure[0][0])+1
            date=datetime.date.today()

            cashier_id=session['id']
            cursor.execute('INSERT INTO EXPENDITURE(EXPENDITURE_ID,DATE,COMMODITY_TYPE,COMMODITY_NAME,DESCRIPTION,PROVIDER,QUANTITY,UNIT_PRICE,TRANSPORT_COST,TRANSACTION_COST,SUBTOTAL,CASHIER_ID)VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',(expenditure_id,date,commodity_type,commodity_name,description,provider,quantity,unit_price,transport_cost,transaction_cost,subtotal,cashier_id))
            mydb.connection.commit()

            bank_transaction_id=(bank_data[0][0])+1
            bank_balance=(bank_data[0][5])-subtotal

            cursor.execute('INSERT INTO ACCOUNT(BANK_TRANSACTION_ID,EXPENSE_ID,AMOUNT_OUT,BALANCE,DATE,TRANSACTION_ID,AMOUNT_IN,MODE)VALUES(%s,%s,%s,%s,%s,%s,%s,%s)',(bank_transaction_id,expenditure_id,subtotal,bank_balance,date,0,0,"EXPENSE"))
            mydb.connection.commit()
        
        if submit=='deposit':
            amount=int(request.form['amount_to_deposit'])
            new_balance=int((bank_data[0][5]))+ int (amount)
            today=datetime.date.today()
            bank_transaction_id=(bank_data[0][0])+1
            cashier_id=session['id']
            cursor.execute('INSERT INTO ACCOUNT(BANK_TRANSACTION_ID,EXPENSE_ID,AMOUNT_OUT,BALANCE,DATE,TRANSACTION_ID,AMOUNT_IN,MODE)VALUES(%s,%s,%s,%s,%s,%s,%s,%s)',(bank_transaction_id,0,0,new_balance,today,0,amount,cashier_id))
            mydb.connection.commit()

        return redirect(url_for('bank'))
        

    return render_template('Bank.html',cashiers=cashiers,transaction_items=transaction_items,bank_data=bank_data,available=available,stockdata=stockdata,products=products,expenditure=expenditure,transactions=transactions)


if __name__ == '__main__':
    app.run(debug=True)