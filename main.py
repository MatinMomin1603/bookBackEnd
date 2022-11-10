from typing import Union
import uvicorn
from fastapi import FastAPI,Request,File,UploadFile,Form
from fastapi.staticfiles import StaticFiles
import pymongo
from bson import ObjectId
import json
import time
app = FastAPI()
app.mount("/images", StaticFiles(directory="images"), name="images")

client = pymongo.MongoClient('localhost', 27017)
db = client["book"]

ip = "http://192.168.1.106"

@app.get("/")
def read_root():
    return "Welcome to book store"

@app.post("/admin/login")
async def adminLogin(request:Request):
    try:
        body = await request.json()
        check = db['admins'].find_one({"email" : body['email'],"password":body['password']})
        if check :
            return {"status" : True ,"message" : "Login success" ,"data":json.loads(json.dumps(check,default=str))}
        else:
            return {"status" : False ,"message" : "Wrong username or password" ,"data":{}}
    except Exception as e:
        return {"status" : False ,"message" : str(e) }

# @app.post("/admin/book")
# async def addBook(request:Request):
#     try:
#         body = await request.json()
#         db['books'].insert_one(body)
#         return {"status" : True ,"message" : "Book added" }
#     except Exception as e:
#         return {"status" : False ,"message" : "Something wrong"}

@app.post("/admin/book")
def fileupload(file:bytes = File(),name: str = Form(),author: str = Form(),description: str = Form()):
    try:
        path = "/images/"+str(int(time.time()))+".jpg"
        with open("."+path,"wb") as f:
            f.write(file)
            f.close()
        db['books'].insert_one({"name":name,"author":author,"description":description,"image":path})
        return {"status":True,"message":"Book added"}
    except Exception as e:
        return {"status" : False ,"message" : str(e) }

@app.get("/admin/book")
def getBooks(request:Request):
    try:
        books = []
        query = {}
        # search regx
        search = request.query_params.get('search')
        if search:
            query = {"$or":[{"name":{"$regex":search}},{"author":{"$regex":search}},{"description":{"$regex":search}}]}

        get = list(db['books'].aggregate([
            {"$match":query},
            {
                '$project': {
                    'name': 1, 
                    'author': 1, 
                    'description': 1, 
                    'image': {
                        '$concat': [
                           ip,'$image'
                        ]
                    }
                }
            }
        ]))
        return {"status" : True ,"message" : "Book fetch success" ,"data" :json.loads(json.dumps(get,default=str))}
    except Exception as e:
        return {"status" : False ,"message" : str(e)}

@app.post("/admin/book/edit")
async def updateBook(request:Request):
    try:
        body = await request.json()
        db['books'].update_one({"_id":ObjectId(body['_id'])},{"$set":{"name":body['name'],"author":body['author'],"description":body['description']}})
        return {"status" : True ,"message" : "Book updated" }
    except Exception as e:
        return {"status" : False ,"message" : str(e)}

@app.post("/user")
async def registerUser(request:Request):
    try:
        body = await request.json()
        db['users'].insert_one({"name":body['name'],"email":body['email'],"password":body['password']})
        return {"status" : True ,"message" : "User registered" }
    except Exception as e:
        return {"status" : False ,"message" : str(e)}

@app.post("/user/login")
async def adminLogin(request:Request):
    try:
        body = await request.json()
        check = db['users'].find_one({"email" : body['email'],"password":body['password']})
        if check :
            return {"status" : True ,"message" : "Login success" ,"data":json.loads(json.dumps(check,default=str))}
        else:
            return {"status" : False ,"message" : "Wrong username or password" ,"data":{}}
    except Exception as e:
        return {"status" : False ,"message" : str(e) }

@app.post("/user/book/view")
async def adminLogin(request:Request):
    try:
        body = await request.json()
        db['book_views'].insert_one({"user_id":ObjectId(body['user_id']),"book_id":ObjectId(body['book_id'])})
        get = list(db['books'].aggregate([
            {"$match":{"_id":ObjectId(body['book_id'])}},
            {
                '$project': {
                    'name': 1,
                    'author': 1,
                    'description': 1,
                    'image': {
                        '$concat': [
                            ip,'$image'
                        ]
                    }
                }
            }
        ]))
        return {"status":True,"data":json.loads(json.dumps(get,default=str))}
    except Exception as e:
        return {"status" : False ,"message" : str(e) }

@app.get("/user/dashboard")
async def adminLogin(request:Request):
    try:
        query = {}
        search = request.query_params.get('search')
        if search:
            query = {"$or":[{"name":{"$regex":search}},{"author":{"$regex":search}},{"description":{"$regex":search}}]}
        get = list (db['books'].aggregate([
            {"$match":query},
            {
                '$lookup': {
                    'from': 'book_views', 
                    'localField': '_id', 
                    'foreignField': 'book_id', 
                    'as': 'result'
                }
            }, {
                '$project': {
                    'name': 1, 
                    'author': 1, 
                    'description': 1, 
                    'view_count': {
                        '$size': '$result'
                    },
                    'image': {
                        '$concat': [
                           ip,'$image'
                        ]
                    }
                }
            }, {
                '$sort': {
                    'view_count': -1
                }
            }
        ]))
        return {"status":True,"data":json.loads(json.dumps(get,default=str))}
    except Exception as e:
        return {"status" : False ,"message" : str(e) }


if __name__ == "__main__":
    uvicorn.run("main:app",host="0.0.0.0", port=80, reload=True)