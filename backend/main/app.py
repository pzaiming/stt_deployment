from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError, OperationalError
from sqlalchemy.orm import sessionmaker
import os
from datetime import datetime
from fastapi.encoders import jsonable_encoder
from typing import Optional
from sqlalchemy import select, and_, text
import pytz

from typing import List
import re

app = FastAPI()

# Database connection URL
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://user:password@db:5432/yourdatabase')
POSTGRES_DB = os.getenv('POSTGRES_DB', 'yourdatabase')

# Create the database engine
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Models for request validation
class UserData(BaseModel):
    circuit: Optional[str] = None
    audio_file_path: Optional[str] = None
    file_name: Optional[str] = None
    duration: Optional[str] = None
    stt_transcript: Optional[str] = None
    gt_transcript: Optional[str] = None
    operator_remark: Optional[str] = None
    start_time: Optional[str] = None
    created: Optional[str] = None
    last_modified: Optional[str] = None
    src: Optional[str] = None
    dst: Optional[str] = None
    bookmark: Optional[str] = None
    mplan: Optional[str] = None
    created_by: Optional[str] = "R5"
    stereo: Optional[bool] = False


class Keyword(BaseModel):
    keyword: Optional[str] = None
    priority_: Optional[int] = None
    service_: Optional[str] = None
    created_by: Optional[str] = "R5"


class UserLogin(BaseModel):
    username: str
    password: str

class NewUser(BaseModel):
    username: str
    password: str

class DeleteUser(BaseModel):
    username: str

def validate_username(username):
    pattern = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_]*$')
    return pattern.match(username) is not None

###### USER LOGIN ##########################################################################################
# Routes

def get_db_session(username: str = None, password: str = None):
    if not username or not password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    test_db_url = f"postgresql://{username}:{password}@db:5432/{POSTGRES_DB}"
    try:
        test_engine = create_engine(test_db_url)
        Session = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
        session = Session()
        return session
    except OperationalError:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.post("/login_user/")
async def login_user(user: UserLogin):
    test_db_url = f"postgresql://{user.username}:{user.password}@db:5432/{POSTGRES_DB}"
    
    try:
        test_engine = create_engine(test_db_url)
        with test_engine.connect() as connection:
            return {"auth": True}
    except OperationalError:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/create_user/")
async def create_user(new_user: NewUser):
    session = SessionLocal()
    username = new_user.username
    password = new_user.password

    if not validate_username(username):
        raise HTTPException(status_code=400, detail="Invalid username")

    password_escaped = password.replace("'", "''")

    try:
        role_exists_query = text("SELECT 1 FROM pg_catalog.pg_roles WHERE rolname = :username")
        role_exists = session.execute(role_exists_query, {'username': username}).fetchone()

        if role_exists:
            raise HTTPException(status_code=400, detail="User already exists")

        create_role_query = f"CREATE ROLE {username} WITH LOGIN PASSWORD '{password_escaped}'"
        session.execute(text(create_role_query))

        create_schema_query = f"CREATE SCHEMA IF NOT EXISTS {username} AUTHORIZATION {username}"
        session.execute(text(create_schema_query))

        grant_schema_query = f"GRANT ALL ON SCHEMA {username} TO {username}"
        session.execute(text(grant_schema_query))

        revoke_schema_query = f"REVOKE ALL ON SCHEMA {username} FROM PUBLIC"
        session.execute(text(revoke_schema_query))

        alter_role_query = f"ALTER ROLE {username} SET search_path = {username}, public"
        session.execute(text(alter_role_query))

        grant_user_data_query = f"GRANT INSERT, UPDATE, DELETE ON TABLE public.user_data TO {username}"
        session.execute(text(grant_user_data_query))

        grant_keywords_query = f"GRANT INSERT, UPDATE, DELETE ON TABLE public.keywords TO {username}"
        session.execute(text(grant_keywords_query))

        session.commit()
        return {"message": "User created successfully"}

    except SQLAlchemyError as e:
        session.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        session.close()

@app.delete("/delete_user/")
async def delete_user(delete_user: DeleteUser):
    session = SessionLocal()
    username = delete_user.username

    if not validate_username(username):
        raise HTTPException(status_code=400, detail="Invalid username")

    try:
        drop_schema_query = f"DROP SCHEMA IF EXISTS {username} CASCADE"
        session.execute(text(drop_schema_query))

        drop_role_privileges_query = f"REVOKE ALL PRIVILEGES ON TABLE public.user_data FROM {username}; REVOKE ALL PRIVILEGES ON TABLE public.keywords FROM {username};"
        session.execute(text(drop_role_privileges_query))
        
        drop_role_query = f"DROP ROLE IF EXISTS {username}"
        session.execute(text(drop_role_query))

        session.commit()
        return {"message": "User deleted successfully"}

    except SQLAlchemyError as e:
        session.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        session.close()

###### USER DATA ##########################################################################################
# Routes
@app.post("/add_user_data/")
async def add_user_data(data: UserData):
    # Convert start_time to datetime and extract Singapore Standard Time components
    singapore_tz = pytz.timezone('Asia/Singapore')
    start_time = datetime.fromisoformat(data.start_time)
    
    # Extract year, month, day, etc.
    start_year = start_time.year
    start_month = start_time.month
    start_day = start_time.day
    start_hour = start_time.hour
    start_minute = start_time.minute
    start_second = start_time.second

    # Automatically set last_modified to the current timestamp
    last_modified = datetime.now(singapore_tz).isoformat(timespec='milliseconds')
    created = last_modified

    # Prepare data dictionary with extracted time components
    data_dict = data.model_dump()
    data_dict.update({
        'start_time': start_time,
        'start_year': start_year,
        'start_month': start_month,
        'start_day': start_day,
        'start_hour': start_hour,
        'start_minute': start_minute,
        'start_second': start_second,
        'created': created,
        'last_modified': last_modified,
    })

    query = """
    INSERT INTO user_data (
        circuit, audio_file_path, file_name, duration, stt_transcript, gt_transcript, 
        operator_remark, start_time, start_year, start_month, start_day, start_hour, 
        start_minute, start_second, created, last_modified, src, dst, bookmark, mplan, created_by, stereo
    ) VALUES (
        :circuit, :audio_file_path, :file_name, :duration, :stt_transcript, :gt_transcript, 
        :operator_remark, :start_time, :start_year, :start_month, :start_day, :start_hour, 
        :start_minute, :start_second, :created, :last_modified, :src, :dst, :bookmark, :mplan, :created_by, :stereo
    )
    """
    
    session = SessionLocal()
    
    try:
        session.execute(text(query), data_dict)
        session.commit()
        return {"message": "User data added successfully"}
    except SQLAlchemyError as e:
        session.rollback()
        print(e)
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        session.close()

@app.delete("/delete_user_data/")
async def delete_user_data(circuit, start_time, file_name):
    session = SessionLocal()
    try:
        delete_query = """
        DELETE FROM user_data 
        WHERE circuit = :circuit AND start_time = :start_time AND file_name = :file_name
        """
        session.execute(text(delete_query), {"circuit": circuit, "start_time": start_time, "file_name": file_name})
        session.commit()
        return {"message": "User data deleted successfully"}
    except SQLAlchemyError as e:
        session.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        session.close()

@app.get("/get_all_user_data/")
async def get_all_user_data(
    latest: int = 0,
    user: str = Query(...),
    password: str = Query(...)
    ):
    
    session = get_db_session(user, password)

    query = "SELECT * FROM user_data"
    if latest:
        query += """
        WHERE (circuit, created) IN (
            SELECT circuit, MAX(created) AS created
            FROM user_data
            GROUP BY circuit
        )
        """

    try:
        result = session.execute(text(query)).mappings()  # Use mappings to convert rows to dictionaries
        rows = result.fetchall()
        return {"data": [dict(row) for row in rows]}  # Convert each row mapping to a dictionary
    except SQLAlchemyError as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        session.close()

@app.get("/filter_user_data/")
async def filter_user_data(
    circuit: Optional[str] = None, 
    operator_remark_contains: Optional[str] = None, 
    src: Optional[str] = None, 
    dst: Optional[str] = None, 
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    bookmark: Optional[str] = None,  # Added bookmark filter
    mplan: Optional[str] = None,  # Added bookmark filter
    user: str = Query(...),
    password: str = Query(...)
):
    end_time_dt = None
    start_time_dt = None

    session = get_db_session(user, password)
    
    # Start building the query
    query = select("*").select_from(text("user_data"))

    # Prepare list of conditions based on input filters
    conditions = []
    
    if circuit:
        conditions.append(text("circuit = :circuit"))
    if operator_remark_contains:
        conditions.append(text("operator_remark LIKE :operator_remark_contains"))
    if src:
        conditions.append(text("src = :src"))
    if dst:
        conditions.append(text("dst = :dst"))
    if start_time:
        start_time_dt = datetime.fromisoformat(start_time)
        if end_time:
            end_time_dt = datetime.fromisoformat(end_time)
            conditions.append(text("start_time BETWEEN :start_time AND :end_time"))
        else:
            conditions.append(text("start_time >= :start_time"))
    if bookmark:
        conditions.append(text("bookmark = :bookmark"))
    if mplan:
        conditions.append(text("bookmark = :bookmark"))

    # Apply the conditions if any filters are present
    if conditions:
        query = query.where(and_(*conditions))

    try:
        # Prepare parameters dictionary for binding
        params = {
            "circuit": circuit,
            "operator_remark_contains": f"%{operator_remark_contains}%" if operator_remark_contains else None,
            "src": src,
            "dst": dst,
            "start_time": start_time_dt if start_time else None,
            "end_time": end_time_dt if end_time else None,
            "bookmark": bookmark,
            "mplan": mplan,
        }

        # Execute query
        result = session.execute(query, params)
        rows = result.fetchall()
        return {"data": [dict(row._mapping) for row in rows]}  # Convert to list of dictionaries
    except SQLAlchemyError as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        session.close()

@app.patch("/update_user_data_partial/")
async def update_user_data_partial(
    circuit: str, 
    start_time: str, 
    file_name: str, 
    data: UserData,
    user: str = Query(...),
    password: str = Query(...)
):
    session = get_db_session(user, password)

    # Get the existing record using the composite primary key
    existing_record_query = """
    SELECT * FROM user_data 
    WHERE circuit = :circuit AND start_time = :start_time AND file_name = :file_name
    """
    existing_record = session.execute(
        text(existing_record_query), 
        {"circuit": circuit, "start_time": start_time, "file_name": file_name}
    ).fetchone()

    if not existing_record:
        raise HTTPException(status_code=404, detail="Record not found")

    # Convert to dict and exclude unset fields
    update_data = jsonable_encoder(data, exclude_unset=True)

    # Automatically update the 'last_modified' field to current time in Singapore Standard Time
    singapore_tz = pytz.timezone('Asia/Singapore')
    update_data["last_modified"] = datetime.now(singapore_tz).isoformat(timespec='milliseconds')

    if update_data:
        set_clauses = ", ".join([f"{key} = :{key}" for key in update_data.keys()])
        query = f"""
        UPDATE user_data 
        SET {set_clauses} 
        WHERE circuit = :circuit 
        AND start_time = :start_time 
        AND file_name = :file_name
        """

        try:
            # Add necessary keys to the update_data dict for the WHERE clause
            update_data["circuit"] = circuit
            update_data["start_time"] = start_time
            update_data["file_name"] = file_name

            session.execute(text(query), update_data)
            session.commit()
            return {"message": "User data updated successfully"}
        except SQLAlchemyError as e:
            session.rollback()
            raise HTTPException(status_code=400, detail=str(e))
        finally:
            session.close()
    else:
        return {"message": "No fields to update"}

@app.get("/unique_values/")
async def unique_values(
    column: str,
    user: str = Query(...),
    password: str = Query(...)
    ):
    def get_unique_values(column: str) -> List[str]:
        session = get_db_session(user, password)
        
        # Validate column to avoid SQL injection by checking against a list of allowed columns
        allowed_columns = {"circuit", "audio_file_path", "file_name", "duration", "stt_transcript", 
                        "gt_transcript", "operator_remark", "start_time", "created", "last_modified", 
                        "src", "dst", "bookmark"}
        if column not in allowed_columns:
            raise HTTPException(status_code=400, detail="Invalid column name")

        # Construct query to get unique values for the specified column
        query = select(text(f"DISTINCT {column}")).select_from(text("user_data"))
        
        try:
            result = session.execute(query)
            unique_values = [row[0] for row in result.fetchall()]  # Extract unique values from result
            return unique_values
        except SQLAlchemyError as e:
            raise HTTPException(status_code=400, detail=str(e))
        finally:
            session.close()

    return {"unique_values": get_unique_values(column)}


###### KEYWORD DATA ##########################################################################################

@app.post("/add_keyword/")
async def add_keyword(
    keyword_data: Keyword,
    user: str = Query(...),
    password: str = Query(...)
):
    session = get_db_session(user, password)

    query = """
    INSERT INTO public.keywords (keyword, priority_, service_, created_by)
    VALUES (:keyword, :priority_, :service_, :created_by)
    """

    print(keyword_data.model_dump())
    try:
        session.execute(text(query), keyword_data.model_dump())
        session.commit()
        return {"message": "Keyword added successfully"}
    except SQLAlchemyError as e:
        session.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        session.close()

@app.get("/get_all_keywords/")
async def get_all_keywords(
    user: str = Query(...),
    password: str = Query(...)
):
    session = get_db_session(user, password)
    query = "SELECT * FROM public.keywords"
    
    try:
        result = session.execute(text(query))
        rows = result.fetchall()
        return {"data": [dict(row._mapping) for row in rows]}  # Convert to list of dictionaries
    except SQLAlchemyError as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        session.close()

@app.delete("/delete_keyword/")
async def delete_keyword(
    keyword: str,
    priority_: int,
    service_: str,
    user: str = Query(...),
    password: str = Query(...),
    created_by: str = Query(...),
):
    session = get_db_session(user, password)
    try:
        delete_query = """
        DELETE FROM public.keywords
        WHERE keyword = :keyword AND priority_ = :priority_ AND service_ = :service_ AND created_by = :created_by
        """
        session.execute(text(delete_query), {"keyword": keyword, "priority_": priority_, "service_": service_, "created_by": created_by})
        session.commit()
        return {"message": "Keyword deleted successfully"}
    except SQLAlchemyError as e:
        session.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        session.close()