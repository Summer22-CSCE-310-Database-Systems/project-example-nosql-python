from flask import Flask, render_template, request

# Initialize Firestore DB
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore


### INSERT YOUR CREDENTIALS FILE HERE
cred = credentials.Certificate('csce310-app-cred.json')
firebase_admin.initialize_app(cred)

db = firestore.client()

app = Flask(__name__)

class FirebaseObject:
    def __init__(self, **kwargs):
        self.created_at = firestore.SERVER_TIMESTAMP
        for key, value in kwargs.items():
            setattr(self, key, value)


class ChefInfo(FirebaseObject):
    __slots__ = ['cname', 'addr', 'phone', 'created_at']
    def __init__(self, **kwargs):
        print(kwargs)
        super().__init__(**kwargs)
    
    def to_dict(self):
        dict_out = {}
        for key in ChefInfo.__slots__:
            dict_out[key] = getattr(self, key)
        return dict_out

class Dish(FirebaseObject):
    __slots__ = ['dname', 'ddetail', 'created_at']
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    
    def to_dict(self):
        dict_out = {}
        for key in Dish.__slots__:
            dict_out[key] = getattr(self, key)
        return dict_out
    
class Cooks(FirebaseObject):
    __slots__ = ['chefid', 'dishid', 'created_at']
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    
    def to_dict(self):
        dict_out = {}
        for key in Cooks.__slots__:
            dict_out[key] = getattr(self, key)
        return dict_out
    
    @staticmethod
    def make_id(chefid, dishid):
        return chefid + ',' + dishid
    
    def id(self):
        return Cooks.make_id(self.chefid, self.dishid)


if __name__ == '__main__':
    app.run()

def getchefs():
    docs = db.collection('ChefInfo').order_by(
    'created_at', direction=firestore.Query.ASCENDING).stream()
    chef_list = []
    for chef in docs:
        chef_dict = chef.to_dict()
        chef_list.append((chef_dict['cname'], chef_dict['addr'], chef_dict['phone']))
    return chef_list

def getdishes():
    docs = db.collection('Dish').order_by(
    'created_at', direction=firestore.Query.ASCENDING).stream()
    dish_list = []
    for dish in docs:
        dish_dict = dish.to_dict()
        dish_list.append((dish_dict['dname'], dish_dict['ddetail']))
    return dish_list

def getcooks():
    docs = db.collection('Cooks').order_by(
    'created_at', direction=firestore.Query.ASCENDING).stream()
    cooks_list = []
    for cooks in docs:
        cooks_dict = cooks.to_dict()
        chef_id = cooks_dict['chefid']
        dish_id = cooks_dict['dishid']

        chef = get_chef_fromid(chef_id).to_dict()
        dish = get_dish_fromid(dish_id).to_dict()
        
        cooks_list += [(chef['cname'], dish['dname'])]
    
    return cooks_list


@app.route('/')
def home():
    return render_template('home.html')


##### CREATE 

def get_chef(chefname):
    chef = db.collection('ChefInfo').where('cname', '==', chefname).limit(1).get()
    if len(chef) == 0 or not chef[0].exists:
        raise('Chef not found')
    return chef[0]

def get_dish(dishname):
    dish = db.collection('Dish').where('dname', '==', dishname).limit(1).get()
    if len(dish) == 0 or not dish[0].exists:
        raise('Dish not found')
    return dish[0]

@app.route("/createchef")
def createchef(feedback_message=None, feedback_type=False):
    return render_template("createchef.html",
            feedback_message=feedback_message, 
            feedback_type=feedback_type)

@app.route("/chefcreate", methods=['POST'])
def chefcreate():
    cname = request.form["cname"]
    addr = request.form["addr"]
    phone = request.form["phone"]

    # Checks for name uniqueness
    try:
        get_chef(cname)
        return createchef(feedback_message='A chef named {} already exists. Create a chef with a different name.'.format(cname), feedback_type=False)
    except Exception as err:
        pass

    try:
        entry = ChefInfo(cname=cname, addr=addr, phone=phone)
        db.collection('ChefInfo').add(entry.to_dict())
        
    except Exception as err:
        return createchef(feedback_message='Database error: {}'.format(err), feedback_type=False)
            

    return createchef(feedback_message='Successfully added chef {}'.format(cname),
                       feedback_type=True)

@app.route("/createdish")
def createdish(feedback_message=None, feedback_type=False):
    return render_template("createdish.html",
            feedback_message=feedback_message, 
            feedback_type=feedback_type)

@app.route("/dishcreate", methods=['POST'])
def dishcreate():
    dname = request.form["dname"]
    ddetail = request.form["ddetail"]

    # Checks for name uniqueness
    try:
        get_dish(dname)
        return createdish(feedback_message='A dish named {} already exists. Create a dish with a different name.'.format(dname), feedback_type=False)
    except Exception as err:
        pass

    try:
        entry = Dish(dname=dname, ddetail=ddetail)
        db.collection('Dish').add(entry.to_dict())
    except Exception as err:
        return createdish(feedback_message='Database error: {}'.format(err), feedback_type=False)

    return createdish(feedback_message='Successfully added dish {}'.format(dname),
                       feedback_type=True)


@app.route("/createcooks")
def createcooks(feedback_message=None, feedback_type=False):
    chef_names = [name for name, _, _ in getchefs()]
    dish_names = [name for name, _ in getdishes()]
    return render_template("createcooks.html", 
                           chefnames=chef_names, 
                           dishnames=dish_names, 
                           feedback_message=feedback_message, 
                           feedback_type=feedback_type)


def get_chef_fromid(chef_id):
    chef = db.collection('ChefInfo').document(chef_id).get()
    if not chef.exists:
        raise('Chef (id {}) not found.'.format(chef_id))
    return chef

def get_dish_fromid(dish_id):
    dish = db.collection('Dish').document(dish_id).get()
    if not dish.exists:
        raise('Dish (id {}) not found.'.format(dish_id))
    return dish


@app.route("/cookscreate", methods=['POST'])
def cookscreate():
    chef_name = request.form.get('chefnames')
    dish_name = request.form.get('dishnames')

    try:
        chef_id = get_chef(chef_name).id
        dish_id = get_dish(dish_name).id
        entry = Cooks(chefid=chef_id, dishid=dish_id)
    except Exception as err:
        return createcooks(feedback_message=err, feedback_type=False)

    # Checks for cooks uniqueness
    prev_cooks = db.collection('Cooks').document(entry.id()).get()
    if prev_cooks.exists:
        return createcooks(feedback_message='A cooks between {} and {} already exists.'.format(chef_name, dish_name), feedback_type=False)

    try:
        db.collection('Cooks').document(entry.id()).set(entry.to_dict())
    except Exception as err:
        return createcooks(feedback_message=err, feedback_type=False)

    return createcooks(feedback_message='Successfully added cooks relationship between {} and {}'.format(chef_name, dish_name),
                       feedback_type=True)

##### READ

@app.route("/readchef")
def readchef():
    chef_list = getchefs()
    
    return render_template("readchef.html", cheflist=chef_list)

@app.route("/readdish")
def readdish():
    dish_list = getdishes()
    return render_template("readdish.html", dishlist=dish_list)

@app.route("/readcooks")
def readcooks():
    cooks_list = getcooks()
    return render_template("readcooks.html", cookslist=cooks_list)


##### UPDATE 

@app.route("/updatechef")
def updatechef(feedback_message=None, feedback_type=False):
    chef_names = [name for name, _, _ in getchefs()]
    return render_template("updatechef.html", 
                           chefnames=chef_names, 
                           feedback_message=feedback_message, 
                           feedback_type=feedback_type)

@app.route("/chefupdate", methods=['POST'])
def chefupdate():
    chef_name = request.form.get('chefnames')
    cname = request.form["cname"]
    addr = request.form["addr"]
    phone = request.form["phone"]

    try:
        batch = db.batch()
        chef_id = get_chef(chef_name).id
        chef_ref = db.collection('ChefInfo').document(chef_id)

        if cname != '':
            batch.update(chef_ref, {'cname': cname})
        if addr != '':
            batch.update(chef_ref, {'addr': addr})
        if phone != '':
            batch.update(chef_ref, {'phone': phone})
        
        batch.commit()
    except Exception as err:
        return updatechef(feedback_message=err, feedback_type=False)

    return updatechef(feedback_message='Successfully updated chef {}'.format(chef_name),
                       feedback_type=True)


@app.route("/updatedish")
def updatedish(feedback_message=None, feedback_type=False):
    dish_names = [name for name, _, in getdishes()]
    return render_template("updatedish.html", 
                           dishnames=dish_names, 
                           feedback_message=feedback_message, 
                           feedback_type=feedback_type)

@app.route("/dishupdate", methods=['POST'])
def dishupdate():
    dish_name = request.form.get('dishnames')
    dname = request.form["dname"]
    ddetail = request.form["ddetail"]

    try:
        batch = db.batch()
        dish_id = get_dish(dish_name).id
        dish_ref = db.collection('Dish').document(dish_id)

        if dname != '':
            batch.update(dish_ref, {'dname': dname})
        if ddetail != '':
            batch.update(dish_ref, {'ddetail': ddetail})
        
        batch.commit()
    except Exception as err:
        return updatedish(feedback_message=err, feedback_type=False)

    return updatedish(feedback_message='Successfully updated dish {}'.format(dish_name),
                       feedback_type=True)


@app.route("/updatecooks")
def updatecooks(feedback_message=None, feedback_type=False):
    chef_names = [name for name, _, _ in getchefs()]
    dish_names = [name for name, _ in getdishes()]
    return render_template("updatecooks.html", 
                           chefnames=chef_names, 
                           dishnames=dish_names, 
                           feedback_message=feedback_message, 
                           feedback_type=feedback_type)


@app.route("/cooksupdate", methods=['POST'])
def cooksupdate():
    chef_name1 = request.form.get('chefnames1')
    dish_name1 = request.form.get('dishnames1')

    chef_name2 = request.form.get('chefnames2')
    dish_name2 = request.form.get('dishnames2')

    try:
        
        chef1_id = get_chef(chef_name1).id
        dish1_id = get_dish(dish_name1).id
        chef2_id = get_chef(chef_name2).id
        dish2_id = get_dish(dish_name2).id

        prev_cooks_id = Cooks.make_id(chef1_id, dish1_id)
        prev_cooks_ref = db.collection('Cooks').document(prev_cooks_id)
        prev_cooks_created_at = prev_cooks_ref.get().to_dict()['created_at']


        new_cooks_id = Cooks.make_id(chef2_id, dish2_id)
        new_cooks_ref = db.collection('Cooks').document(new_cooks_id)
        
        # First creates a new cooks with updated chef_id, dish_id and cooks_id; while keeping the created_at attribute.
        # Then deletes the old cooks.
        # All done atomically, in a batch write.
        batch = db.batch()
        batch.set(new_cooks_ref, {'chefid': chef2_id, 'dishid': dish2_id, 'created_at': prev_cooks_created_at})
        batch.delete(prev_cooks_ref)
        batch.commit()
    except Exception as err:
        return updatecooks(feedback_message=err, feedback_type=False)

    return updatecooks(feedback_message='Successfully updated cooks relationship from ({} and {}) to ({} and {})'.format(chef_name1, dish_name1, chef_name2, dish_name2),
                       feedback_type=True)


#### DELETE

def get_cooks_with_chef(chef_id):
    return [doc.id for doc in db.collection('Cooks').where('chefid', '==', chef_id).stream()]

def get_cooks_with_dish(dish_id):
    return [doc.id for doc in db.collection('Cooks').where('dishid', '==', dish_id).stream()]

@app.route("/deletechef")
def deletechef(feedback_message=None, feedback_type=False):
    chef_names = [name for name, _, _ in getchefs()]
    return render_template("deletechef.html", 
                           chefnames=chef_names, 
                           feedback_message=feedback_message, 
                           feedback_type=feedback_type)

@app.route("/chefdelete", methods=['POST'])
def chefdelete():
    if not request.form.get('confirmInput'):
        return deletechef(feedback_message='Operation canceled. Chef not deleted.', feedback_type=False)
    
    chef_name = request.form.get('chefnames')

    try:
        chef_id = get_chef(chef_name).id
        cooks_with_chef = get_cooks_with_chef(chef_id)
        batch = db.batch()
        
        for cooks_id in cooks_with_chef:
            batch.delete(db.collection('Cooks').document(cooks_id)) # cascade delete

        chef_ref = db.collection('ChefInfo').document(chef_id)
        batch.delete(chef_ref)

        batch.commit()
    except Exception as err:
        return deletechef(feedback_message=err, feedback_type=False)

    return deletechef(feedback_message='Successfully deleted chef {}'.format(chef_name),
                       feedback_type=True)


@app.route("/deletedish")
def deletedish(feedback_message=None, feedback_type=False):
    dish_names = [name for name, _ in getdishes()]
    return render_template("deletedish.html", 
                           dishnames=dish_names, 
                           feedback_message=feedback_message, 
                           feedback_type=feedback_type) 

@app.route("/dishdelete", methods=['POST'])
def dishdelete():
    if not request.form.get('confirmInput'):
        return deletedish(feedback_message='Operation canceled. Dish not deleted.', feedback_type=False)
    
    dish_name = request.form.get('dishnames')

    try:
        dish_id = get_dish(dish_name).id
        cooks_with_dish = get_cooks_with_dish(dish_id)
        batch = db.batch()
        
        for cooks_id in cooks_with_dish:
            batch.delete(db.collection('Cooks').document(cooks_id)) # cascade delete

        dish_ref = db.collection('Dish').document(dish_id)
        batch.delete(dish_ref)

        batch.commit()
    except Exception as err:
        return deletedish(feedback_message=err, feedback_type=False)

    return deletedish(feedback_message='Successfully deleted dish {}'.format(dish_name),
                       feedback_type=True)


@app.route("/deletecooks")
def deletecooks(feedback_message=None, feedback_type=False):
    chef_names = [name for name, _, _ in getchefs()]
    dish_names = [name for name, _ in getdishes()]
    return render_template("deletecooks.html", 
                           chefnames=chef_names, 
                           dishnames=dish_names, 
                           feedback_message=feedback_message, 
                           feedback_type=feedback_type)

@app.route("/cooksdelete", methods=['POST'])
def cooksdelete():
    chef_name = request.form.get('chefnames')
    dish_name = request.form.get('dishnames')

    try:
        chef_id = get_chef(chef_name).id
        dish_id = get_dish(dish_name).id

        cooks_id = Cooks.make_id(chef_id, dish_id)
        cooks_ref = db.collection('Cooks').document(cooks_id)

        if not cooks_ref.get().exists:
            msg = 'Cooks relationship between {} and {} not found.'.format(chef_name, dish_name)
            return deletecooks(feedback_message=msg, feedback_type=False)
        
        cooks_ref.delete()
    except Exception as err:
        return deletecooks(feedback_message=err, feedback_type=False)

    return deletecooks(feedback_message='Successfully deleted cooks relationship between {} and {}'.format(chef_name, dish_name),
                       feedback_type=True)
