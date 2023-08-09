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
app.config['MYSQL_DB']='PHARMACY_BORU'

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
            cursor.execute('SELECT * from STOCK_TABLE')
            counter=cursor.fetchall()
            Sold_items=[]
            for num in counter:
                sold_item=[]
                sold_item.append(num[0])
                sold_item.append(str(request.form[str(num[0])]))
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
            #Get last Sales_ID
            cursor=mydb.connection.cursor()
            cursor.execute('SELECT SALES_ID FROM SALES')
            last_sales_id=int(cursor.fetchall()[-1][0])
            
            sale_date=str(datetime.date.today())
            total_cost=0
            #Get stocks_data
            cursor=mydb.connection.cursor()
            cursor.execute('SELECT * FROM STOCK_TABLE')
            last_stocks_data=cursor.fetchall()
            #Get Product cost for each ID
            
            for stockID in Sold_items:
                if int(stockID[1]) == 0:
                    pass
                else:
                    cursor=mydb.connection.cursor()
                    cursor.execute('SELECT PRODUCT_ID FROM STOCK_TABLE WHERE STOCK_ID='+str(stockID[0]))
                    prod_id=cursor.fetchall()[0][0]
                    cursor=mydb.connection.cursor()
                    cursor.execute('SELECT * FROM DRUG_DETAILS WHERE DRUG_ID='+str(prod_id))
                    cost_drug_name=cursor.fetchall()
                    cost=cost_drug_name[0][7]
                    drug_name=cost_drug_name[0][1]
                    #Get subtotal
                    subtotal=int(cost)*int(stockID[1])
                    total_cost=total_cost+int(subtotal)
                    #Add to Transaction_Items
                    #Get last Transaction_item_id
                    cursor=mydb.connection.cursor()
                    cursor.execute('SELECT TRANSACTION_ITEM_ID FROM TRANSACTION_ITEMS')
                    last_Titem_id=cursor.fetchall()[-1][0]
                    print(last_Titem_id)
                    last_Titem_id=int(last_Titem_id)+1
                    #insert into Transaction_item_id
                    cursor.execute('INSERT INTO TRANSACTION_ITEMS(TRANSACTION_ITEM_ID,TRANSACTION_ID,QUANTITY,UNIT_PRICE,PRODUCT_NAME,SUBTOTAL)VALUES(%s,%s,%s,%s,%s,%s)',(last_Titem_id,last_transaction_id,stockID[1],cost,drug_name,subtotal))
                    mydb.connection.commit()
                    #insert into SALES
                    last_sales_id=int(last_sales_id)+1
                    cursor.execute('INSERT INTO SALES(SALES_ID,STOCK_ID,SALES_DATE,QUANTITY,UNIT_PRICE,TOTAL_AMOUNT)VALUES(%s,%s,%s,%s,%s,%s)',(last_sales_id,stockID[0],sale_date,stockID[1],cost,subtotal))
                    mydb.connection.commit()

                    #Submit into the account
                    cursor.execute('SELECT * from ACCOUNT')
                    Bank_Account=cursor.fetchall()
                    Bank_balance=int(Bank_Account[-1][5])+subtotal
                    last_bank_id=int(Bank_Account[-1][0])+1
                    cursor.execute('INSERT INTO ACCOUNT(BANK_TRANSACTION_ID,SALE_ID,AMOUNT_IN,BALANCE,DATE,EXPENSE_ID,AMOUNT_OUT,DEBIT)VALUES(%s,%s,%s,%s,%s,%s,%s,%s)',(last_bank_id,last_sales_id,subtotal,Bank_balance,sale_date,0,0," "))
                    mydb.connection.commit()

                    #deduct from stocks_table[rem_stock]
                    cursor.execute('SELECT REM_STOCK FROM STOCK_TABLE WHERE STOCK_ID='+str(stockID[0]))
                    rem_stock=int(cursor.fetchall()[0][0])
                    rem_stock=rem_stock-int(stockID[1])
                    cursor.execute(f'UPDATE STOCK_TABLE SET REM_STOCK={rem_stock} WHERE STOCK_ID={stockID[0]}')
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
    #list Down DrugDetails & stock
    cursor.execute('SELECT * FROM DRUG_DETAILS')
    drug_details=cursor.fetchall()
    
    cursor.execute('SELECT * FROM STOCK_TABLE')
    stocks=cursor.fetchall()
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

    return render_template('order2.html',partial_pay_data=partial_pay_data,stocks=stocks,drug_details=drug_details, past_transaction_items=past_transaction_items,past_transactions=past_transactions,today=today,expiry_range=expiry_range)

@app.route('/products' ,methods=['POST','GET'] )
def products():
    if 'fullname' in session:

        #date
        today=datetime.date.today()
        #drug details
        cursor=mydb.connection.cursor()
        cursor.execute('SELECT * FROM DRUG_DETAILS')
        drug_details=cursor.fetchall()
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
        #suppliers
        cursor.execute('SELECT * FROM SUPPLIERS ORDER BY SUPPLIER_ID DESC')
        suppliers=cursor.fetchall()
        cursor.execute('SELECT * FROM SUPPLIERS')
        suppliersNew=cursor.fetchall()
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
                drugId=request.form['drugId']
                drugQuantity=request.form['Quantity']
                drugBP=request.form['drugBP']
                drugSP=request.form['drugSP']
                drug_ExpiryDate=request.form['drug_ExpiryDate']
                stock_id=int(stockdata[-1][0])+1
                drug_supplier=request.form['supplier']
                today=datetime.date.today()
                xxx=drug_ExpiryDate.split('-')
                x=datetime.date(int(xxx[0]),int(xxx[1]),int(xxx[2]))
                print(x)
                if today>x:
                    msg='The drug is already expired'
                    print(msg)
                    #correction 4/8/2023
                    cursor.execute('INSERT INTO STOCK_TABLE(STOCK_ID,PRODUCT_ID,SUPPLIER_ID,STOCK_DATE,EXPIRY_DATE,QUANTITY,STAFF_ID,BP,REM_STOCK)VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)',(stock_id,drugId,drug_supplier,today,drug_ExpiryDate,drugQuantity,staffId,drugBP,drugQuantity))
                    mydb.connection.commit()
                    #update SellingPrice
                    cursor.execute(f'UPDATE DRUG_DETAILS SET COST={drugSP} WHERE DRUG_ID={drugId}')
                    mydb.connection.commit()
                else:
                    #correction 4/8/2023
                    cursor.execute('INSERT INTO STOCK_TABLE(STOCK_ID,PRODUCT_ID,SUPPLIER_ID,STOCK_DATE,EXPIRY_DATE,QUANTITY,STAFF_ID,BP,REM_STOCK)VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)',(stock_id,drugId,drug_supplier,today,drug_ExpiryDate,drugQuantity,staffId,drugBP,drugQuantity))
                    mydb.connection.commit()
                    #update SellingPrice
                    cursor.execute(f'UPDATE DRUG_DETAILS SET COST={drugSP} WHERE DRUG_ID={drugId}')
                    mydb.connection.commit()

                    # Remove money from the account
                    subtotal=int(drugBP)*int(drugQuantity)
                    bank_transaction_id=(bank_data[0][0])+1
                    bank_balance=(bank_data[0][5])-subtotal
                    expenditure_id=int(expenditure[0][0])+1
                    cursor.execute('INSERT INTO EXPENDITURE(EXPENDITURE_ID,DATE,COMMODITY_TYPE,COMMODITY_NAME,DESCRIPTION,PROVIDER,QUANTITY,UNIT_PRICE,TRANSPORT_COST,TRANSACTION_COST,SUBTOTAL)VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',(expenditure_id,today,'RESTOCK',' ','','',drugQuantity,drugBP,0,0,subtotal))
                    mydb.connection.commit()

                    cursor.execute('INSERT INTO ACCOUNT(BANK_TRANSACTION_ID,EXPENSE_ID,AMOUNT_OUT,BALANCE,DATE,SALE_ID,AMOUNT_IN,DEBIT)VALUES(%s,%s,%s,%s,%s,%s,%s,%s)',(bank_transaction_id,expenditure_id,subtotal,bank_balance,today,0,0," "))
                    mydb.connection.commit()
                    

            elif submit=='addNewDrug':
                DrugId=int(drug_details[-1][0])+1
                DrugName=request.form['drugName']
                DrugCategory=request.form['drugCategory']
                DrugBrand=request.form['drugBrand']
                DrugDosage=request.form['dosage']
                DrugStrength=request.form['drugStrength']
                DrugCost=request.form['drugCost']
                mode=request.form['mode']
                presence='no'
                for drugs in drug_details:
                    if DrugName==drugs[1]:
                        if DrugCategory==drugs[2]:
                            if DrugBrand==drugs[3]:
                                presence='yes'
                if presence=='no':
                    cursor.execute('INSERT INTO DRUG_DETAILS(DRUG_ID,DRUG_NAME,CATEGORY,BRAND,DOSAGE,STRENGTH,STATUS,COST,MODE)VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)',(DrugId,DrugName,DrugCategory,DrugBrand,DrugDosage,DrugStrength,'yes',DrugCost,mode))
                    mydb.connection.commit()
                    #Update UserLog
                    cursor.execute('SELECT * FROM USER_LOG ORDER BY LOG_ID DESC')
                    last_log_id=int(cursor.fetchall()[-1][0])+1
                    
                    cursor.execute('INSERT INTO USER_LOG(LOG_ID,DRUG_ID,USER_ID,DATE,ACTIVITY)VALUES(%s,%s,%s,%s,%s)',(last_log_id,DrugId,staffId,today,'ADD'))
                    mydb.connection.commit()

                else:
                    print('The drug already exists')
            elif submit=='delete_drug':
                DrugId=request.form['drugId']
                cursor.execute('DELETE FROM DRUG_DETAILS WHERE DRUG_ID="'+DrugId+'"')
                mydb.connection.commit()
                cursor.execute('DELETE FROM STOCK_TABLE WHERE PRODUCT_ID="'+DrugId+'"')
                mydb.connection.commit()
                #Update UserLog
                cursor.execute('SELECT * FROM USER_LOG ORDER BY LOG_ID DESC')
                last_log_id=int(cursor.fetchall()[-1][0])+1
                cursor.execute('INSERT INTO USER_LOG(LOG_ID,DRUG_ID,USER_ID,DATE,ACTIVITY)VALUES(%s,%s,%s,%s,%s)',(last_log_id,DrugId,staffId,today,'DELETE'))
                mydb.connection.commit()
                
            elif submit=='delete_stock':
                print('delete stock')
                StockId=request.form['StockId']
                print(StockId)
                cursor.execute('DELETE FROM STOCK_TABLE WHERE STOCK_ID="'+StockId+'"')
                mydb.connection.commit()
                #Update UserLog
                cursor.execute('SELECT * FROM USER_LOG ORDER BY LOG_ID DESC')
                last_log_id=int(cursor.fetchall()[-1][0])+1
                cursor.execute('INSERT INTO USER_LOG(LOG_ID,STOCK_ID,USER_ID,DATE,ACTIVITY)VALUES(%s,%s,%s,%s,%s)',(last_log_id,StockId,staffId,today,'DELETE'))
                mydb.connection.commit()

            elif submit=='AddNewSupplier':
                cursor.execute('SELECT * FROM SUPPLIERS')
                suppliersNew=cursor.fetchall()
                SupplierId = int(suppliersNew[-1][0]) + 1
                print(SupplierId)
                supplierName = request.form["SupplierName"]
                contactNumber = request.form['contact']
                location=request.form['location']
                
                cursor.execute('INSERT INTO SUPPLIERS(SUPPLIER_ID,SUPPLIER_NAME,CONTACT,LOCATION)VALUES(%s,%s,%s,%s)',(SupplierId,supplierName,contactNumber,location))
                mydb.connection.commit()
                #Update UserLog
                cursor.execute('SELECT * FROM USER_LOG ORDER BY LOG_ID DESC')
                last_log_id=int(cursor.fetchall()[-1][0])+1
                cursor.execute('INSERT INTO USER_LOG(LOG_ID,SUPPLIER_ID,USER_ID,DATE,ACTIVITY)VALUES(%s,%s,%s,%s,%s)',(last_log_id,SupplierId,staffId,today,'ADD'))
                mydb.connection.commit()


            elif submit=='delete_supplier':
                supplierId=request.form['SupplierId']
                cursor.execute('DELETE FROM SUPPLIERS WHERE SUPPLIER_ID="'+supplierId+'"')
                mydb.connection.commit()
                #Update UserLog
                cursor.execute('SELECT * FROM USER_LOG ORDER BY LOG_ID DESC')
                last_log_id=int(cursor.fetchall()[-1][0])+1
                cursor.execute('INSERT INTO USER_LOG(LOG_ID,SUPPLIER_ID,USER_ID,DATE,ACTIVITY)VALUES(%s,%s,%s,%s,%s)',(last_log_id,supplierId,staffId,today,'DELETE'))
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
                last_log_id=int(cursor.fetchall()[-1][0])+1
                cursor.execute('INSERT INTO USER_LOG(LOG_ID,MEMBER_ID,USER_ID,DATE,ACTIVITY)VALUES(%s,%s,%s,%s,%s)',(last_log_id,IdNumber,staffId,today,'ADD'))
                mydb.connection.commit()
                        
            elif submit=='delete_Member':
                memberId=request.form['memberID']
                cursor.execute('UPDATE USERS SET ACTIVE="OFF" WHERE USER_ID="'+memberId+'"')
                mydb.connection.commit()
                #Update UserLog
                cursor.execute('SELECT * FROM USER_LOG ORDER BY LOG_ID DESC')
                last_log_id=int(cursor.fetchall()[-1][0])+1
                cursor.execute('INSERT INTO USER_LOG(LOG_ID,MEMBER_ID,USER_ID,DATE,ACTIVITY)VALUES(%s,%s,%s,%s,%s)',(last_log_id,memberId,staffId,today,'DELETE'))
                mydb.connection.commit()

            elif submit=='ACTIVATE':
                memberId=request.form['memberID']
                cursor.execute('UPDATE USERS SET ACTIVE="ON" WHERE USER_ID="'+memberId+'"')
                mydb.connection.commit()
                #Update UserLog
                cursor.execute('SELECT * FROM USER_LOG ORDER BY LOG_ID DESC')
                last_log_id=int(cursor.fetchall()[-1][0])+1
                cursor.execute('INSERT INTO USER_LOG(LOG_ID,MEMBER_ID,USER_ID,DATE,ACTIVITY)VALUES(%s,%s,%s,%s,%s)',(last_log_id,memberId,staffId,today,'ADD'))
                mydb.connection.commit()
                


            return redirect(url_for('products'))

        else:
            pass
    else:
        return redirect(url_for('signin'))
    
    return render_template('products.html',msg=msg,today=today,expiry_range=expiry_range,managerCheck=managerCheck,drug_details=drug_details,suppliers=suppliers,users=users,stockdata=stockdata,stockdataDesc=stockdataDesc)


@app.route('/accounts' ,methods=['POST','GET'] )
def accounts():
    if 'fullname' in session:
        #user info
        user_id=session['id']
        cursor=mydb.connection.cursor()
        cursor.execute(f'SELECT * FROM USERS WHERE USER_ID={user_id}')
        user=cursor.fetchall()[0]


        cursor.execute(f'SELECT COUNT(*) FROM TRANSACTION WHERE CASHIER_ID={user_id}')
        Drugs_Sold=cursor.fetchall()[0][0]

        cursor.execute(f'SELECT COUNT(*) FROM STOCK_TABLE WHERE STAFF_ID={user_id}')
        RestocksMade=cursor.fetchall()[0][0]

        cursor.execute(f'SELECT COUNT(*) FROM TRANSACTION WHERE CASHIER_ID={user_id}')
        Drugs_Sold=cursor.fetchall()[0][0]

        cursor.execute(f'SELECT COUNT(DRUG_ID) FROM USER_LOG WHERE USER_ID={user_id} AND ACTIVITY="DELETE" ')
        Drugs_deleted=cursor.fetchall()[0][0]

        cursor.execute(f'SELECT COUNT(DRUG_ID) FROM USER_LOG WHERE USER_ID={user_id} AND ACTIVITY="ADD" ')
        Drugs_added=cursor.fetchall()[0][0]

        cursor.execute(f'SELECT COUNT(STOCK_ID) FROM USER_LOG WHERE USER_ID={user_id} AND ACTIVITY="DELETE" ')
        stocks_Deleted=cursor.fetchall()[0][0]

        cursor.execute(f'SELECT COUNT(SUPPLIER_ID) FROM USER_LOG WHERE USER_ID={user_id} AND ACTIVITY="ADD" ')
        Suppliers_added=cursor.fetchall()[0][0]

        cursor.execute(f'SELECT COUNT(SUPPLIER_ID) FROM USER_LOG WHERE USER_ID={user_id} AND ACTIVITY="DELETE" ')
        Suppliers_deleted=cursor.fetchall()[0][0]

        cursor.execute(f'SELECT COUNT(MEMBER_ID) FROM USER_LOG WHERE USER_ID={user_id} AND ACTIVITY="ADD" ')
        members_added=cursor.fetchall()[0][0]

        cursor.execute(f'SELECT COUNT(MEMBER_ID) FROM USER_LOG WHERE USER_ID={user_id} AND ACTIVITY="DELETE" ')
        members_deleted=cursor.fetchall()[0][0]

        cursor.execute(f'SELECT * FROM USERS WHERE TITLE="CASHIER" ')
        cashiers=cursor.fetchall()

    else:
        return redirect(url_for('signin'))
    return render_template('accounts.html',cashiers=cashiers,user=user,members_deleted=members_deleted,members_added=members_added,Suppliers_deleted=Suppliers_deleted,Suppliers_added=Suppliers_added,stocks_Deleted=stocks_Deleted,Drugs_added=Drugs_added,Drugs_deleted=Drugs_deleted,Drugs_Sold=Drugs_Sold,RestocksMade=RestocksMade)

@app.route('/<cashier_id>' ,methods=['POST','GET'] )
def accounts_cashier(cashier_id):
    if 'fullname' in session:
        #user info
        
        user_id=session['id']
        cursor=mydb.connection.cursor()
        cursor.execute(f'SELECT * FROM USERS WHERE USER_ID={cashier_id}')
        user=cursor.fetchall()[0]


        cursor.execute(f'SELECT COUNT(*) FROM TRANSACTION WHERE CASHIER_ID={cashier_id}')
        Drugs_Sold=cursor.fetchall()[0][0]

        cursor.execute(f'SELECT COUNT(*) FROM STOCK_TABLE WHERE STAFF_ID={cashier_id}')
        RestocksMade=cursor.fetchall()[0][0]

        cursor.execute(f'SELECT COUNT(*) FROM TRANSACTION WHERE CASHIER_ID={cashier_id}')
        Drugs_Sold=cursor.fetchall()[0][0]

        cursor.execute(f'SELECT COUNT(DRUG_ID) FROM USER_LOG WHERE USER_ID={cashier_id} AND ACTIVITY="DELETE" ')
        Drugs_deleted=cursor.fetchall()[0][0]

        cursor.execute(f'SELECT COUNT(DRUG_ID) FROM USER_LOG WHERE USER_ID={cashier_id} AND ACTIVITY="ADD" ')
        Drugs_added=cursor.fetchall()[0][0]

        cursor.execute(f'SELECT COUNT(STOCK_ID) FROM USER_LOG WHERE USER_ID={cashier_id} AND ACTIVITY="DELETE" ')
        stocks_Deleted=cursor.fetchall()[0][0]

        cursor.execute(f'SELECT COUNT(SUPPLIER_ID) FROM USER_LOG WHERE USER_ID={cashier_id} AND ACTIVITY="ADD" ')
        Suppliers_added=cursor.fetchall()[0][0]

        cursor.execute(f'SELECT COUNT(SUPPLIER_ID) FROM USER_LOG WHERE USER_ID={cashier_id} AND ACTIVITY="DELETE" ')
        Suppliers_deleted=cursor.fetchall()[0][0]

        cursor.execute(f'SELECT COUNT(MEMBER_ID) FROM USER_LOG WHERE USER_ID={cashier_id} AND ACTIVITY="ADD" ')
        members_added=cursor.fetchall()[0][0]

        cursor.execute(f'SELECT COUNT(MEMBER_ID) FROM USER_LOG WHERE USER_ID={cashier_id} AND ACTIVITY="DELETE" ')
        members_deleted=cursor.fetchall()[0][0]

        cursor.execute(f'SELECT * FROM USERS WHERE TITLE="CASHIER" ')
        cashiers=cursor.fetchall()

    else:
        return redirect(url_for('signin'))
    return render_template('cashiers.html',user_id=user_id,cashiers=cashiers,user=user,members_deleted=members_deleted,members_added=members_added,Suppliers_deleted=Suppliers_deleted,Suppliers_added=Suppliers_added,stocks_Deleted=stocks_Deleted,Drugs_added=Drugs_added,Drugs_deleted=Drugs_deleted,Drugs_Sold=Drugs_Sold,RestocksMade=RestocksMade)


@app.route('/store',methods=['GET','POST'])
def store():
    cursor=mydb.connection.cursor()
    #Suppliers
    cursor.execute('SELECT * FROM SUPPLIERS ORDER BY SUPPLIER_ID DESC')
    supplier_data=cursor.fetchall()
    #stock_id desc
    cursor.execute('SELECT * FROM STOCK_TABLE ORDER BY STOCK_ID DESC')
    stockdataDesc=cursor.fetchall()

    cursor.execute('SELECT * FROM DRUG_DETAILS')
    drug_details=cursor.fetchall()
    print(stockdataDesc,drug_details)
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
    
    return render_template('store.html',supplier_data=supplier_data,today=today,expiry_range=expiry_range,stockdataDesc=stockdataDesc,drug_details=drug_details)

@app.route('/bank',methods=['POST','GET'])
def bank():
    cursor = mydb.connection.cursor()
    cursor.execute('SELECT * FROM ACCOUNT ORDER BY BANK_TRANSACTION_ID DESC')
    bank_data=cursor.fetchall()

    cursor.execute('SELECT * FROM EXPENDITURE ORDER BY EXPENDITURE_ID DESC')
    expenditure=cursor.fetchall()

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

            if subtotal > available:
                print('cant obtain more than available')
                return redirect(url_for('bank'))


            cursor.execute('INSERT INTO EXPENDITURE(EXPENDITURE_ID,DATE,COMMODITY_TYPE,COMMODITY_NAME,DESCRIPTION,PROVIDER,QUANTITY,UNIT_PRICE,TRANSPORT_COST,TRANSACTION_COST,SUBTOTAL)VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',(expenditure_id,date,commodity_type,commodity_name,description,provider,quantity,unit_price,transport_cost,transaction_cost,subtotal))
            mydb.connection.commit()

            bank_transaction_id=(bank_data[0][0])+1
            bank_balance=(bank_data[0][5])-subtotal

            cursor.execute('INSERT INTO ACCOUNT(BANK_TRANSACTION_ID,EXPENSE_ID,AMOUNT_OUT,BALANCE,DATE,SALE_ID,AMOUNT_IN,DEBIT)VALUES(%s,%s,%s,%s,%s,%s,%s,%s)',(bank_transaction_id,expenditure_id,subtotal,bank_balance,date,0,0," "))
            mydb.connection.commit()
        
        if submit=='deposit':
            amount=int(request.form['amount_to_deposit'])
            new_balance=float((bank_data[0][5]))+ float (amount)
            today=datetime.date.today()
            bank_transaction_id=(bank_data[0][0])+1
            cursor.execute('INSERT INTO ACCOUNT(BANK_TRANSACTION_ID,EXPENSE_ID,AMOUNT_OUT,BALANCE,DATE,SALE_ID,AMOUNT_IN,DEBIT)VALUES(%s,%s,%s,%s,%s,%s,%s,%s)',(bank_transaction_id,0,0,new_balance,today,0,amount," "))
            mydb.connection.commit()

        return redirect(url_for('bank'))
        

    return render_template('Bank.html',bank_data=bank_data,available=available)


if __name__ == '__main__':
    app.run(debug=True)