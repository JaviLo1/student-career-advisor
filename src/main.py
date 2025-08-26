#igual que el 2.3, con el output modificado para revertir el orden

import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from openai import OpenAI

#funcion importar google sheets
def ini_google_sheet(service_account_file, spreadsheet_id, range_names):
    # Scopes required by the API
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

    # Authenticate and create the service client
    creds = Credentials.from_service_account_file(
            service_account_file, scopes=SCOPES)
    service = build('sheets', 'v4', credentials=creds)

    # Call the Sheets API and return the data
    results = {}
    # Iterate through the range names and get data for each
    for range_name in range_names:
        result = service.spreadsheets().values().get(spreadsheetId=spreadsheet_id,
                                                     range=range_name).execute()
        results[range_name] = result.get('values', [])

    return results

#funcion sacar puestos IJ en funcion de rama actividad IJ
def find_top_3_matches_with_column_details(data, range_name, input_string):
    if range_name not in data:
        return []

    range_data = data[range_name]
    matching_rows = []

    # Find matches in column A and validate data in columns C, D, E
    for row in range_data[1:]:  # Skip header row
        if len(row) >= 5 and row[0] == input_string:
            try:
                # Convert C, D, E to numbers; B is a string
                numeric_value_C = float(row[2])
                numeric_value_D = float(row[3])
                numeric_value_E = float(row[4])
                matching_rows.append((row[1], numeric_value_C, numeric_value_D, numeric_value_E))
            except ValueError:
                # Skip rows with invalid numeric data
                continue

    # Sort the matching rows based on column E values, and select top 3
    top_3_matches = sorted(matching_rows, key=lambda x: x[3], reverse=True)[:3]

    return top_3_matches

#equivalencia puestos IJ a WEF
def retrieve_from_column_a_using_column_b_matches(data, range_name_7, column_b_values):
    if range_name_7 not in data:
        return []

    matching_strings_from_column_a = []

    for row in data[range_name_7][1:]:  # Skip header row
        # Check if column B is not blank and is in column_b_values
        if len(row) > 1 and row[1].strip() and row[1].strip() in column_b_values:
            # Add the corresponding value from column A to the list
            # If column A is blank, append None
            matching_strings_from_column_a.append(row[0].strip() if len(row) > 0 and row[0].strip() else None)

    return matching_strings_from_column_a

#Sacar datos de crecimiento de puestos de WEF
def match_and_categorize(data, range_name_8, matching_strings):
    if range_name_8 not in data:
        return []

    categorized_results = []

    for match in matching_strings:
        for row in data[range_name_8][1:]:  # Skip header row
            if len(row) > 1 and row[0].strip() == match:
                value = float(row[1].replace(',', '.'))  # Replace comma with dot for decimal
                category = categorize_value(value)
                categorized_results.append((match, category))
                break  # Break the loop once a match is found

    return categorized_results

#pasar de porcentaje a texto (puestos WEF)
def categorize_value(value):
    if value in [-37.5, -25]:
        return "decrecimiento alto"
    elif value in [-12.5, -6.25]:
        return "decrecimiento moderado"
    elif value == 0:
        return "estable"
    elif value in [6.25, 12.5]:
        return "crecimiento moderado"
    elif value in [18.75, 25]:
        return "crecimiento acentuado"
    elif value in [31.25, 37.5]:
        return "crecimiento máximo"
    else:
        return "valor desconocido"

#llamada api chatgpt devuelve 1 proyecto por sector indicado, incluye objetivos y objetivos ODS
def query_project_recommendation(input1, input2, input3, input4, api_key):
    client = OpenAI(api_key=api_key)

    message = f"Actua como asesor académico. Tu tarea es generar 1 proyecto por cada uno de los 3 sectores indicados. Cada sector está delimitado por “,” . \
        La dificultad de los proyectos se debe de corresponder con la de un estudiante universitario, ten en cuenta las limitaciones debido a sus estudios y que el proyecto debe estar enfocado a dichos estudios, realizable en 300 horas. Los proyectos deben de ser concretos, \
        específicos y realistas y deben de estar ajustados al perfil del estudiante que se muestra a continuación: Hola, soy estudiante de {input1}. \
        Quiero enfocar mi carrera a los siguientes sectores: {input2}. Mis gustos son: {input3} , {input4}. \
        Por cada proyecto incluye: el título del proyecto, una breve descripcion, los objetivos a cumplir, los objetivos ODS relacionados y una breve planificación. \
        La respuesta debe de estar estructurada de la siguiente manera: \
        1. Título del proyecto:  \
        Descripción: \
        Objetivos: (lista objetivos) \
        Objetivos ODS: (lista objetivos ODS) \
        Planificación: (lista fases)\
        Un ejemplo de titulo de proyecto es el siguiente: Carrera: Ingenieria; Desarrollo de una herramienta basada en inteligencia artificial \
        generativa (OpenAI) para la recomendación de temas de TFG/M innovadores para estudiantes.\
        carrera: derecho; El Papel del Derecho en la Prevención del Crimen: Estrategias Innovadoras"

    chat_completion = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": message}]
    )

    return chat_completion.choices[0].message.content

#llamada api chatgpt, devuelve 3 sectores en funcion del perfil del estudiante
def query_sector_selection(student_profile, sectors, api_key):
    client = OpenAI(api_key=api_key)

    sectors_str = sectors
    message = f" Tu tarea es elegir 3 sectores de la siguiente lista {sectors_str}. Cada sector esta delimitado por ; \
        La eleccion de los sectores tiene que estar basada en los que mas se ajusten al siguiente perfil estudiantil: {student_profile}, \
        a continuación te doy un ejemplo de respuesta. Responde siempre en el mismo formato: \
        Cuidado Servicios Personales y Bienestar,  Automotriz y Aeroespacial, Medios Entretenimiento y Deportes"

    chat_completion = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": message}]
    )

    return chat_completion.choices[0].message.content

#para sacar sector churn
def find_value_next_to_match(data, range_name, search_string):
    # Iterate through each row in the data
    if range_name not in data:
        return None  # Return None if the range name is not found

    range_data = data[range_name]
    # Iterate through each row in the range data
    for row in range_data:
        # Check if the first column matches the search string
        if len(row) > 0 and row[0] == search_string:
            # Return the values in columns B, E, and F
            column_b = row[1] if len(row) > 1 else None
            column_e = row[4] if len(row) > 4 else None
            column_f = row[5] if len(row) > 5 else None
            return column_b, column_e, column_f
    return None  # Return None if no match is found

#para sacar competencias en funcion del sector
def find_highest_values_in_matching_row(data, range_name, search_string, column_index, num_values=3):
    if range_name not in data:
        return []  # Return an empty list if the range name is not found

    range_data = data[range_name]
    headers = range_data[0]  # Assuming the first row contains headers
    for row in range_data[1:]:  # Skip the header row
        if len(row) > column_index and row[column_index] == search_string:
            numeric_values = [(i, x) for i, x in enumerate(row[1:], start=1) if x.isdigit()]
            highest_values = sorted(numeric_values, key=lambda x: int(x[1]), reverse=True)[:num_values]
            return [(headers[i], value) for i, value in highest_values]

    return []

def split_string_into_three(input_string):
    # Split the string into parts using the comma as a separator
    parts = input_string.split(',')

    # Check if the string contains at least 3 parts
    if len(parts) < 3:
        raise ValueError("The input string does not contain enough commas to split into three parts.")

    # Trim leading and trailing spaces from each part and assign them
    first_part = parts[0].strip()
    second_part = parts[1].strip()
    third_part = ','.join(parts[2:]).strip()

    # Remove the dot at the end of the third part, if present
    if third_part.endswith('.'):
        third_part = third_part[:-1]

    return first_part, second_part, third_part

# Definiciones api google sheets
SERVICE_ACCOUNT_FILE1 = 'REPLACE_WITH_YOUR_SERVICE_ACCOUNT_JSON_PATH'  # e.g., /path/to/service-account.json
SPREADSHEET_ID1 = 'REPLACE_WITH_YOUR_SPREADSHEET_ID'
RANGE_NAME1 = 'Sectores-Competencias-WEF!A1:AA19'
RANGE_NAME2 = 'perfilestudiantecompleto!C1:D26'
RANGE_NAME3 = 'SectoresGlobalesWEF!A1:F20'
RANGE_NAME4 = 'empleosdatos!A1:B101'
RANGE_NAME5 = 'ocupados_españa!A1:H39691'
RANGE_NAME6 = 'Ramas_Puestos_IJ!A1:E181'
RANGE_NAME7 = 'empleos!A1:E181'
RANGE_NAME8 = 'empleosdatos!A1:D101'
range_names = [RANGE_NAME1, RANGE_NAME2, RANGE_NAME3, RANGE_NAME4, RANGE_NAME5, RANGE_NAME6, RANGE_NAME7, RANGE_NAME8]

#Definiciones api chatgpt
api_key = "REPLACE_WITH_YOUR_OPENAI_API_KEY"

#perfil estudiante
rama_puesto_IJ = 'Ingenierias y Tecnicas'
carrera = "Máster Ingeniería Telecomunicaciones "
gustos = "Deporte y música "
tecnologias = "5G, Inteligencia Articifical, Machine Learning"
student_profile =  f"estudios universitarios: {carrera}  gustos personales: {gustos}  tecnologías en las que esta interesado {tecnologias} "
sectors = "Medios Entretenimiento y Deportes; Gobierno y Sector Público; Tecnología de la Información y Comunicaciones Digitales; \
Sector Inmobiliario; Servicios Financieros; Cadena de Suministro y Transporte; Organizaciones No Gubernamentales y de Membresía; \
Educación y Formación; Cuidado Servicios Personales y Bienestar; Agricultura y Recursos Naturales; Servicios Profesionales; \
Infraestructura; Salud y Atención Sanitaria; Venta al por Menor y al por Mayor de Bienes de Consumo; Energía y Materiales; \
Manufactura; Automotriz y Aeroespacial; Alojamiento Alimentación y Ocio"

#inicialización sheets
data = ini_google_sheet(SERVICE_ACCOUNT_FILE1, SPREADSHEET_ID1, range_names)

#accedo con la rama a los puestos
top3_puestosIJ = find_top_3_matches_with_column_details(data, RANGE_NAME6, rama_puesto_IJ)

#los separo para acceder al wef
puestos_aislados = [row[0] for row in top3_puestosIJ]

#accedo a los puestos del wef
matching_data = retrieve_from_column_a_using_column_b_matches(data, RANGE_NAME7, puestos_aislados)

#paso de porcentaje a escala propia
categorized_results = match_and_categorize(data, RANGE_NAME8, matching_data)

#saco sectores en funcion del perfil del alumno
sector_selection = query_sector_selection(student_profile, sectors, api_key)

sector1, sector2, sector3 = split_string_into_three(sector_selection)


result2 = find_value_next_to_match(data, RANGE_NAME3, sector1)

result3 = find_value_next_to_match(data, RANGE_NAME3, sector2)

result4 = find_value_next_to_match(data, RANGE_NAME3, sector3)

column_index = 0  # 0 -> columna A
highest_values1 = find_highest_values_in_matching_row(data, RANGE_NAME1, sector1, column_index)

highest_values2 = find_highest_values_in_matching_row(data, RANGE_NAME1, sector2, column_index)

highest_values3 = find_highest_values_in_matching_row(data, RANGE_NAME1, sector3, column_index)


#saco tematicas de tfm con objetivos y obj ods en funcion del perfil del alumno
projects = query_project_recommendation(carrera, sector_selection, gustos, tecnologias, api_key)

print(sector_selection)
print(carrera)
print(gustos)
print(tecnologias)
print("\n")
print("Te proponemos las siguientes temáticas con objetivos incluidos que puedes usar para realizar tu tfx:\n")
print(projects)


# Print or process the results (puestos con mas vacantes)

print("\n \nEn base a tu perfil te proporcionamos la siguiente información: \n ")
print("Puestos que creemos que se ajustan a tu perfil:\n")
for row in top3_puestosIJ:
    formatted_row = f"Posición: {row[0]} | Vacantes: {row[1]} | Competencia: {row[2]} | Salario Medio: {row[3]}"
    print(formatted_row)  # Each row contains data from columns B, C, D, and E
print("Los datos mostrados son a nivel nacional (Fuente: InfoJobs)\n")

# Print de las posiciones WEF
# Initialize an empty set to keep track of printed tuples
printed_tuples = set()

for result in categorized_results:
    # Check if the entire result tuple has already been printed
    if result not in printed_tuples:
        print(result[0],": Se estima un", result[1], "de la demanda para este puesto en los próximos 5 años")
        # Add the result tuple to the set of printed tuples
        printed_tuples.add(result)
print("Los datos mostrados son a nivel global (Fuente: World Economic Forum)\n \n")

print("Hemos identificado estos sectores que creemos que te pueden resultar interesantes en base a tu perfil:\n")

if result2 is not None:
    column_b1, column_e1, column_f1 = result2
    print(f"Sector: {sector1}: Se estima una rotación de puestos en este sector del {column_b1}%")
    print(f"A nivel nacional, la tendencia y el nivel actual de ocupados son los siguientes: {column_e1} puestos por año. Ocupados actuales: {column_f1}\n")

else:
    print(f"No match found for '{sector1}'")



print(f"Competencias relacionadas con el sector: {sector1}")
if highest_values1:
    for header, value in highest_values1:
        print(f"Competencia: {header}, El {value}% de empresas consideran que se va a incrementar la demanda de esta competencia")
else:
    print("No matching row found.")

print("\n")



if result3 is not None:
    column_b2, column_e2, column_f2 = result3
    print(f"Sector: {sector2}, Se estima una rotación de puestos en este sector del {column_b2}%")
    print(f"A nivel nacional la tendencia y el nivel actual de ocupados son los siguientes: {column_e2} puestos por año. Ocupados actuales: {column_f2}\n")
else:
    print(f"No match found for '{sector2}'")


print(f"Competencias relacionadas con el sector: {sector2}")
if highest_values2:
    for header, value in highest_values2:
        print(f"Competencia: {header}, El {value}% de empresas consideran que se va a incrementar la demanda de esta competencia")
else:
    print("No matching row found.")

print("\n")



if result4 is not None:
    column_b3, column_e3, column_f3 = result4
    print(f"Sector: {sector3}, Se estima una rotación de puestos en este sector del {column_b3}%")
    print(f"A nivel nacional la tendencia y el nivel actual de ocupados son los siguientes: {column_e3} puestos por año. Ocupados actuales: {column_f3}\n")
else:
    print(f"No match found for '{sector3}'")


print(f"Competencias relacionadas con el sector: {sector3}")
if highest_values3:
    for header, value in highest_values3:
        print(f"Competencia: {header}, El {value}% de empresas consideran que se va a incrementar la demanda de esta competencia")
else:
    print("No matching row found.")

print("Los datos de rotación son a nivel global (Fuente: World Economic Forum & INE)\n")
print("\n \n")
