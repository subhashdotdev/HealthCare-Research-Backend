from passlib.context import CryptContext



pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")



def construct_query(terms, operators,country,patient_cohort):
    query_parts = []
    print(terms)
    for i in range(len(terms)):
        term = f'{terms[i].strip()}'  
        query_parts.append(term)
        
        if i < len(operators):  
            operator = operators[i]
            query_parts.append(operator)
            
    if country.strip():
        query_parts.append(f'AND {country.strip()}')
    if patient_cohort.strip():
        query_parts.append(f'AND {patient_cohort.strip()}')
    
    query_string = " ".join(query_parts).upper()
    print("query_string",query_string)
    return query_string




def hash_password(password: str) -> str:
    return pwd_context.hash(password)



def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)
