from flask import Flask, render_template, request, jsonify, redirect, url_for
from datetime import datetime, timedelta
import hashlib
from pymongo import MongoClient
import certifi
import jwt
from bson import ObjectId

SECRET_KEY = 'goaqil'

client = MongoClient("mongodb+srv://test:sparta@cluster0.rxufawr.mongodb.net/?retryWrites=true&w=majority", tlsCAFile=certifi.where())  
db = client['dbFINALPROJECT']
app =  Flask(__name__)

@app.route('/')
def index():
    return render_template("index.html")


@app.route('/admin/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form["email"]
        password = request.form["password"]
        pw_hash = hashlib.sha256(password.encode("utf-8")).hexdigest()
        
        result = db.admin.find_one(
            {
                "email": email,
                "password": pw_hash,
            }
        )
        
        if result:
            payload = {
                "id": email,
                "role": 'admin',
                "exp": datetime.utcnow() + timedelta(seconds=60 * 60 * 24),
            }
            token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")

            return jsonify(
                {
                    "result": "success",
                    "token": token,
                }
            )
    
        else:
            return jsonify(
                {
                    "result": "fail",
                    "msg": "We could not find a user with that id/password combination",
                }
            )
    
    msg = request.args.get("msg")
    return render_template("admin/login.html", msg=msg)

@app.route('/admin/dashboard', methods=['GET', 'POST'])
def dashboard_admin():
    token_receive = request.cookies.get("mytoken")
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])

        if payload['role'] != 'admin':
            if payload['role'] == 'dosen':
                return redirect(url_for('login_dosen'), msg="You are not aligible as Admin!")
            elif payload['role'] == 'mahasiswa':
                return redirect(url_for('login_mahasiswa'), msg="You are not aligible as Admin!")

        user_info = db.admin.find_one({"email": payload['id']})
        # ngambil data
        # menambahkan
        
        return render_template('admin/dashboard.html', user_info=user_info)
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect('/admin/login')


@app.route('/admin/data_dosen', methods=['GET', 'POST'])
def data_dosen():
    token_receive = request.cookies.get("mytoken")
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])
        user_info = db.admin.find_one({"email": payload['id']})
        
        data_dosen = list(db.dosen.find({}))

        for data in data_dosen:
            data['_id'] = str(data['_id'])

        return render_template("admin/data_dosen.html", user_info=user_info, data_dosen=data_dosen)
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect('/admin/login')
    

@app.route('/admin/tambah_data_dosen', methods=['GET', 'POST'])
def tambah_data_dosen():
    token_receive = request.cookies.get("mytoken")
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])
        user_info = db.admin.find_one({"email": payload['id']})
    
        if request.method == 'POST':
            #  an api endpoint for signing up
            nip = request.form.get('nip')
            nama_dosen = request.form.get("nama_dosen")
            email = request.form.get("email")
            no_hp = request.form.get("no_hp")
            password = request.form.get("password")
            pw_hash = hashlib.sha256(password.encode("utf-8")).hexdigest()

            # we should save the user to the database
            doc = {
                "nip": nip,                               
                "password": pw_hash,                                                        
                "profile_pic": "",                                         
                "profile_pic_real": "profile_pic/profile_placeholder.png", 
                "nama_dosen": nama_dosen,
                "email" : email,
                "no_hp" : no_hp,

            }
            db.dosen.insert_one(doc)
            return jsonify({"result": "success"})
    
        return render_template("admin/tambah_data_dosen.html")
    
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect('/admin/login')

@app.route('/admin/edit_data_dosen/<id_dosen>', methods=['GET', 'POST'])
def edit_data_dosen(id_dosen):
    token_receive = request.cookies.get("mytoken")
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])
        user_info = db.admin.find_one({"email": payload['id']})
        
        if request.method == "GET":
            data = db.dosen.find_one({'_id' : ObjectId(id_dosen)})
            data['_id'] = str(data['_id'])

            return render_template("admin/edit_data_dosen.html", user_info=user_info, data=data)
        
        db.dosen.update_one(
            {'_id' : ObjectId(id_dosen)},
            {'$set' : {
                'nip' : request.form.get('nip'),
                'nama_dosen' : request.form.get('nama_dosen'),
                'no_hp' : request.form.get('no_hp'),
                'email' : request.form.get('email'),
            }}
        )

        return jsonify({'msg' : 'success'})

    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect('/admin/login')
    
@app.route('/admin/reset_password_dosen/<id_dosen>', methods=['GET', 'POST'])
def reset_password_dosen(id_dosen):
    token_receive = request.cookies.get("mytoken")
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])
        user_info = db.dosen.find_one({"nip": payload['id']})
        
        if request.method == "GET":
            data = db.dosen.find_one({'_id' : ObjectId(id_dosen)})
            data['_id'] = str(data['_id'])

            return render_template("admin/reset_password_dosen.html", user_info=user_info, data=data)
     
        pw_hash = hashlib.sha256(request.form.get('newpassword').encode("utf-8")).hexdigest()
        db.dosen.update_one(
            {'_id' : ObjectId(id_dosen)},
            {'$set' : {
                'password' : pw_hash,
            }}
        )
        return jsonify({'msg' : 'success'})

    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect('/admin/login')

@app.route('/admin/hapus_data_dosen/<id_dosen>')
def delete_data_dosen(id_dosen):
    token_receive = request.cookies.get("mytoken")
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])
        user_info = db.admin.find_one({"email": payload['id']})
        
        db.dosen.delete_one({'_id' : ObjectId(id_dosen)})

        return redirect('/admin/data_dosen')
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect('/admin/login')
    
@app.route('/admin/data_dosen/search', methods=["POST"])
def search_dosen_by_name():
    token_receive = request.cookies.get("mytoken")
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])
        user_info = db.admin.find_one({"email": payload['id']})
        
        search = request.form.get('search')

        data_dosen = list(db.dosen.find({}))
        filtered_data = list()

        for data in data_dosen:
            if search.lower() in data['nama_dosen'].lower():
                data['_id'] = str(data['_id'])
                filtered_data.append(data)

        return jsonify(filtered_data)
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect('/admin/login')

@app.route('/admin/data_mhs', methods=['GET', 'POST'])
def data_mahasiswa():
    token_receive = request.cookies.get("mytoken")
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])
        user_info = db.mahasiswa.find_one({"nim": payload['id']})
        
        data_mhs = list(db.mahasiswa.find({}))

        for data in data_mhs:
            data['_id'] = str(data['_id'])

        return render_template("admin/data_mhs.html", user_info=user_info, data_mhs=data_mhs)
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect('/admin/login')

@app.route('/admin/tambah_data_mhs', methods=['GET', 'POST'])
def tambah_data_mhs():
    token_receive = request.cookies.get("mytoken")
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])
        user_info = db.mahasiswa.find_one({"nim": payload['id']})
    
        if request.method == 'POST':
            #  an api endpoint for signing up
            nim = request.form.get('nim')
            nama_mhs = request.form.get("nama_mhs")
            semester = request.form.get("semester")
            email = request.form.get("email")
            no_hp = request.form.get("no_hp")
            password = request.form.get("password")
            pw_hash = hashlib.sha256(password.encode("utf-8")).hexdigest()

            # we should save the user to the database
            doc = {
                "nim": nim,                               
                "password": pw_hash,
                "semester": semester,                                                        
                "profile_pic": "",                                         
                "profile_pic_real": "profile_pic/profile_placeholder.png", 
                "nama_mhs": nama_mhs,
                "email" : email,
                "no_hp" : no_hp,

            }
            db.mahasiswa.insert_one(doc)
            return jsonify({"result": "success"})
    
        return render_template("admin/tambah_data_mhs.html")
    
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect('/admin/login')

@app.route('/admin/edit_data_mhs/<id_mhs>', methods=['GET', 'POST'])
def edit_data_mhs(id_mhs):
    token_receive = request.cookies.get("mytoken")
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])
        user_info = db.admin.find_one({"email": payload['id']})
        
        if request.method == "GET":
            data = db.mahasiswa.find_one({'_id' : ObjectId(id_mhs)})
            data['_id'] = str(data['_id'])

            return render_template("admin/edit_data_mhs.html", user_info=user_info, data=data)
        
        db.mahasiswa.update_one(
            {'_id' : ObjectId(id_mhs)},
            {'$set' : {
                'nim' : request.form.get('nim'),
                'nama_mhs' : request.form.get('nama_mhs'),
                'semester' : request.form.get('semester'),
                'no_hp' : request.form.get('no_hp'),
                'email' : request.form.get('email'),
            }}
        )

        return jsonify({'msg' : 'success'})

    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect('/admin/login')


@app.route('/admin/hapus_data_mhs/<id_mhs>')
def delete_data_mhs(id_mhs):
    token_receive = request.cookies.get("mytoken")
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])
        user_info = db.admin.find_one({"email": payload['id']})
        
        db.mahasiswa.delete_one({'_id' : ObjectId(id_mhs)})

        return redirect('/admin/data_mhs')
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect('/admin/login')
    
@app.route('/admin/data_mhs/search', methods=["POST"])
def search_mhs_by_name():
    token_receive = request.cookies.get("mytoken")
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])
        user_info = db.admin.find_one({"email": payload['id']})
        
        search = request.form.get('search')

        data_mhs = list(db.mahasiswa.find({}))
        filtered_data = list()

        for data in data_mhs:
            if search.lower() in data['nama_mhs'].lower():
                data['_id'] = str(data['_id'])
                filtered_data.append(data)

        return jsonify(filtered_data)
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect('/admin/login')


@app.route('/admin/profil', methods=['GET', 'POST'])
def profil():
    token_receive = request.cookies.get("mytoken")
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])
        user_info = db.admin.find_one({"email": payload['id']})
        
        profil = list(db.admin.find({}))

        for data in profil:
            data['_id'] = str(data['_id'])

        return render_template("admin/profil.html", user_info=user_info, profil=profil)
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect('/admin/login')

@app.route('/dosen/login', methods=['GET', 'POST'])
def login_dosen():
    if request.method == 'POST':
        nip = request.form["nip"]
        password = request.form["password"]
        pw_hash = hashlib.sha256(password.encode("utf-8")).hexdigest()
        
        result = db.dosen.find_one(
            {
                "nip": nip,
                "password": pw_hash,
            }
        )
        if result:
            payload = {
                "id": nip,
                "role": 'dosen',
                "exp": datetime.utcnow() + timedelta(seconds=60 * 60 * 24),
            }
            token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")

            return jsonify(
                {
                    "result": "success",
                    "token": token,
                }
            )
        else:
            return jsonify(
                {
                    "result": "fail",
                    "msg": "We could not find a user with that id/password combination",
                }
            )
    msg = request.args.get("msg")
    return render_template("dosen/login_dsn.html", msg=msg)

@app.route('/dosen/dashboard', methods=['GET', 'POST'])
def dashboard_dosen():
    token_receive = request.cookies.get("mytoken")
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])

        if payload['role'] != 'dosen':
            if payload['role'] == 'admin':
                return redirect(url_for('login_dosen'), msg="You are not aligible as Dosen!")
            elif payload['role'] == 'mahasiswa':
                return redirect(url_for('login_mahasiswa'), msg="You are not aligible as Dosen!")

        user_info = db.dosen.find_one({"nip": payload['id']})
        # ngambil data
        # menambahkan
        
        return render_template('dosen/dashboard_dsn.html', user_info=user_info)
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect('/dosen/login')

@app.route('/dosen/mk_dosen', methods=['GET', 'POST'])
def mk_dosen():
        token_receive = request.cookies.get("mytoken")
        try:
            payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])

            data_mk = list(db.mk.find({}))

            for data in data_mk:
                data['_id'] = str(data['_id'])
            
            return render_template("dosen/mk_dosen.html", data_mk=data_mk)
        except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
            return redirect('/dosen/login')
    # return render_template("dosen/mk_dsn.html")

@app.route('/dosen/tambah_mk_dosen', methods=['GET', 'POST'])
def tambah_mk_dosen():
    token_receive = request.cookies.get("mytoken")
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])
        user_info = db.dosen.find_one({"nip": payload['id']})
    
        if request.method == 'POST':
            #  an api endpoint for signing up
            nama_mk= request.form.get('nama_mk')
            kode_mk = request.form.get("kode_mk")
            semester = request.form.get("semester")
            dsn_pengampu = request.form.get("dsn_pengampu")
            desc = request.form.get("desc")
            sks = request.form.get("sks")

            # we should save the user to the database
            doc = {
                "nama_mk": nama_mk,   
                "kode_mk": kode_mk,  
                "semester": semester,  
                "dsn_pengampu": dsn_pengampu,
                "desc": desc,
                "sks" : sks                                
            }
            db.mk.insert_one(doc)
            return jsonify({"result": "success"})
    
        return render_template("dosen/tambah_mk_dosen.html")
    
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect('/dosen/login')
   

@app.route('/dosen/hapus_mk/<id_mk>', methods=['GET', 'POST'])
def hapus_mk_dosen(id_mk):
    token_receive = request.cookies.get("mytoken")
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])
        user_info = db.dosen.find_one({"nip": payload['id']})
        
        db.mk.delete_one({'_id' : ObjectId(id_mk)})

        return redirect('/dosen/mk_dosen')
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect('/dosen/login')

@app.route('/dosen/modul', methods=['GET', 'POST'])
def modul_dosen():
    token_receive = request.cookies.get("mytoken")
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])

        data_modul = list(db.modul.find({}))

        for data in data_modul:
            data['_id'] = str(data['_id'])
            
        return render_template("dosen/modul_dsn.html", data_modul=data_modul)
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect('/dosen/login')
        
@app.route('/dosen/tambah_modul_dosen', methods=['GET', 'POST'])
def tambah_modul_dosen():
    token_receive = request.cookies.get("mytoken")
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])
        user_info = db.dosen.find_one({"nip": payload['id']})
    
        if request.method == 'POST':
            #  an api endpoint for signing up
            nama_modul= request.form.get('nama_modul')
            desc = request.form.get("desc")
          
            # we should save the user to the database
            doc = {
                "nama_modul": nama_modul,   
                "desc": desc,  
                                           
            }
            db.modul.insert_one(doc)
            return jsonify({"result": "success"})
    
        return render_template("dosen/tambah_modul_dsn.html")
    
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect('/dosen/login')
    return render_template("dosen/tambah_modul_dsn.html")

@app.route('/dosen/hapus_modul/<id_modul>', methods=['GET', 'POST'])
def hapus_modul(id_modul):
    token_receive = request.cookies.get("mytoken")
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])
        user_info = db.dosen.find_one({"nip": payload['id']})
        
        db.modul.delete_one({'_id' : ObjectId(id_modul)})

        return redirect('/dosen/modul')
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect('/dosen/login')

@app.route('/dosen/modul2', methods=['GET', 'POST'])
def modul2_dosen():
    token_receive = request.cookies.get("mytoken")
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])

        # data_modul = list(db.modul.find({}))

        # for data in data_modul:
        #     data['_id'] = str(data['_id'])
            
        return render_template("dosen/modul2_dsn.html")
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect('/dosen/login')

@app.route('/dosen/tugas_modul', methods=['GET', 'POST'])
def tugas_dosen():
    return render_template("dosen/tugas_dsn.html")

@app.route('/dosen/profil_dosen', methods=['GET'])
def profil_dosen():
        token_receive = request.cookies.get("mytoken")
        try:
            payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])
            # print(payload)

            user_info = db.dosen.find_one({"nip": payload['id']})
            # print(user_info)

            user_info['_id'] = str(user_info['_id'])
            

            return render_template("dosen/profil_dsn.html", user_info=user_info)
        except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
            return redirect('/dosen/dashboard')
        
@app.route('/mahasiswa/login', methods=['GET', 'POST'])
def login_mahasiswa():
        if request.method == 'POST':
            nim = request.form["nim"]
            password = request.form["password"]
            pw_hash = hashlib.sha256(password.encode("utf-8")).hexdigest()
            
            result = db.mahasiswa.find_one(
                {
                    "nim": nim,
                    "password": pw_hash,
                }
            )
            if result:
                payload = {
                    "id": nim,
                    "role": 'mahasiswa',
                    "exp": datetime.utcnow() + timedelta(seconds=60 * 60 * 24),
                }
                token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")

                return jsonify(
                    {
                        "result": "success",
                        "token": token,
                    }
                )
            else:
                return jsonify(
                    {
                        "result": "fail",
                        "msg": "We could not find a user with that id/password combination",
                    }
                )
        msg = request.args.get("msg")
        return render_template("mahasiswa/login_mhs.html", msg=msg)

@app.route('/mahasiswa/dashboard', methods=['GET', 'POST'])
def dashboard_mahasiswa():
    token_receive = request.cookies.get("mytoken")
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])

        if payload['role'] != 'mahasiswa':
            if payload['role'] == 'admin':
                return redirect(url_for('login_dosen'), msg="You are not aligible as Mahasiswa!")
            elif payload['role'] == 'dosen':
                return redirect(url_for('login_mahasiswa'), msg="You are not aligible as Mahasiswa")

        user_info = db.dosen.find_one({"nim": payload['id']})
        # ngambil data
        # menambahkan
        
        return render_template('mahasiswa/dashboard_mhs.html', user_info=user_info)
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect('/mahasiswa/login')
    
@app.route('/mahasiswa/mk', methods=['GET', 'POST'])
def mk_mahasiswa():
    return render_template("mahasiswa/mk_mahasiswa.html")

@app.route('/mahasiswa/modul_mhs', methods=['GET', 'POST'])
def modul_mhs():
    return render_template("mahasiswa/modul_mhs.html")

@app.route('/mahasiswa/modul2_mhs', methods=['GET', 'POST'])
def modul2_mhs():
    return render_template("mahasiswa/modul2_mhs.html")

@app.route('/mahasiswa/tugas', methods=['GET', 'POST'])
def tugas_mhs():
    return render_template("mahasiswa/tugas_mhs.html")

@app.route('/mahasiswa/profil', methods=['GET'])
def profil_mhs():
        token_receive = request.cookies.get("mytoken")
        try:
            payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])
            print(payload)
            user_info = db.mahasiswa.find_one({"nim": payload['id']})
            # print(user_info)

            user_info['_id'] = str(user_info['_id'])
            

            return render_template("mahasiswa/profil_mhs.html", user_info=user_info)
        except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
            return redirect('/mahasiswa/dashboard')

@app.route('/mahasiswa/rekap_nilai', methods=['GET', 'POST'])
def rekap_nilai():
    return render_template("mahasiswa/rekap_nilai.html")


if __name__ == '__main__':
    app.run("0.0.0.0", port=5000, debug=True)

    