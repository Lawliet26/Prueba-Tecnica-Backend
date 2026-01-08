from django.shortcuts import render
import psycopg2
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from langchain_huggingface import HuggingFaceEmbeddings

# Create your views here.

#Cargar modelo de embeddings
embeddings_model = HuggingFaceEmbeddings(
    model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)

@csrf_exempt
def retriever_view(request):
    if request.method == 'POST':
        try:
            #Parsear datos
            data = json.loads(request.body)
            resumen_busqueda = data.get('resumen_busqueda', '')
            
            #Generar embedding
            query_embedding = embeddings_model.embed_query(resumen_busqueda)
            
            #Conexion db
            conn = psycopg2.connect(
                dbname = 'Temarios', user='postgres', password='admin', host='localhost'
            )
            
            cur = conn.cursor()
            
            # Búsqueda usando el operador <=> (distancia coseno)
            # Traemos el contenido, la URL (que ya está separada) y el ID
            embedding_str = '[' + ','.join(map(str, query_embedding)) + ']'
            cur.execute(f"""
                SELECT contenido_texto, url_evidencia, tema_academia_id, 
                    (embedding <=> '{embedding_str}'::vector) AS distancia
                FROM temas_academia_fragmentos
                ORDER BY distancia ASC
                LIMIT 5;
            """)
            
            results = cur.fetchall()
            
            # Formateo respuesta
            output_fragmentos = []
            for res in results:
                output_fragmentos.append({
                    "contenido":res[0],
                    "url":res[1],
                    "academia_id": res[2],
                    "score":1-res[3]
                })
                
            cur.close()
            conn.close()
            
            return JsonResponse({'status':'success', 'fragmentos': output_fragmentos})
    
        except Exception as e:
            return JsonResponse({'status':'error', 'message': str(e)}, status = 500)
    return JsonResponse({"status": "only_post_allowed"}, status = 405)
            
