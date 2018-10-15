from flask import Flask, render_template, request, send_file
from werkzeug import secure_filename
import os, re
import pandas
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
from geopy.exc import GeocoderServiceError
from socket import gaierror
from urllib.error import URLError

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/success", methods=['POST'])
def success():
    try:
        global file
        required=['ID', 'Country', 'Town', 'Address', 'Name', 'Employees']
        if request.method == 'POST':
            file=request.files["file"]

            if "text/csv" in file.mimetype:
                print("we have CSV")
                file.save(secure_filename("uploaded_"+file.filename))

                with open(secure_filename("uploaded_"+file.filename),"r") as f1:
                    content=f1.readlines()

                with open(secure_filename("uploaded_edited_"+file.filename),"w") as f2: # remove empty lines

                    for line in content:
                        match = re.search("^,*$", line)
                        if match == None :
                            f2.write(line)

                with open(os.path.join("templates","dataframe.html"),"w") as f3: #
                    df1=pandas.read_csv(secure_filename("uploaded_edited_"+file.filename))
                    headers = list(df1.columns)
                    #print(f'headers: {headers}')
                    #df1.columns = headers

                    missing=str(set(headers)-set(required))

                    #print("r-s"+str(set(required)-set(headers)))
                    #print("s-r"+str(set(headers)-set(required)))

                    if len(set(required)-set(headers)) == 0:
                        #df1=df1.iloc[1:,]
                        df1.set_index("ID")

                        geolocator = Nominatim(user_agent="geocoder")

                        try:
                            location = geolocator.geocode("Mountain View, CA")
                        except:
                            message="Error: geocode failed on test location: Mountain View, CA"
                            #print(message)
                            return render_template("index.html", error="error_connection.html", message=message)
                            #print("Error: geocode failed on input "+ location)

                        geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1)

                        df1["Coordinates"] = df1["Address"].apply(geocode)
                        df1["Latitude"] = df1["Coordinates"].apply(lambda x: x.latitude if x != None else None)
                        df1["Longitude"] = df1["Coordinates"].apply(lambda x: x.longitude if x != None else None)
                        df1=df1.drop(['Coordinates'], axis=1)

                        df1.to_csv(secure_filename("coordinates_"+file.filename))
                        #print(df1)

                        f3.write('<table>\n')
                        f3.write(' <tr>\n')
                        f3.write('  <th>ID</th>\n')
                        f3.write('  <th>Address</th>\n')
                        f3.write('  <th>Name</th>\n')
                        f3.write('  <th>Employees</th>\n')
                        f3.write('  <th>Latitude</th>\n')
                        f3.write('  <th>Longitude</th>\n')
                        f3.write('  <th>Google Maps</th>\n')
                        f3.write(' </tr>\n')
                        for i in range(0,df1.shape[0]):
                            f3.write(' <tr>\n')
                            f3.write("  <td>"+str(list(df1["ID"])[i])+"</td>\n")
                            f3.write("  <td>"+str(list(df1["Address"])[i])+"</td>\n")
                            f3.write("  <td>"+str(list(df1["Name"])[i])+"</td>\n")
                            f3.write("  <td>"+str(list(df1["Employees"])[i])+"</td>\n")
                            f3.write("  <td>"+str(list(df1["Latitude"])[i])+"</td>\n")
                            f3.write("  <td>"+str(list(df1["Longitude"])[i])+"</td>\n")
                            if str(list(df1["Latitude"])[i]) == "nan":
                                f3.write("  <td>"+str(list(df1["Latitude"])[i])+"</td>\n")
                            else:
                                f3.write('  <td><a href="http://maps.google.com/maps?q='+str(list(df1["Latitude"])[i])+','+str(list(df1["Longitude"])[i])+'" target="_blank">link</a></td>\n')
                            f3.write(' </tr>\n')
                        f3.write('</table>')

                    else:
                        missing= list(set(required)-set(headers))
                        missing_str=""

                        #print("len: "+str(len(missing)))

                        for i in range(0,len(missing)):
                            #print(missing[i])
                            missing_str+=missing[i]+","

                        #print("missing_str: "+missing_str[:-1])

                        return render_template("index.html", error="error_col.html", missing_str=missing_str[:-1], filename=file.filename)
            else:
                return render_template("index.html", error="error.html")

        return render_template("index.html", uploaded="uploaded.html", dataframe="dataframe.html", download="download.html", filename=file.filename)

    except:
        missing_str="except"
        return render_template("index.html", error="error_col.html, missing=missing_str")

@app.route("/error")
def error():
    render_template("error.html")

@app.route("/dataframe")
def dataframe():
    render_template("dataframe.html")

@app.route("/download")
def download():
    return send_file((secure_filename("coordinates_"+file.filename)), attachment_filename="yourfile.csv", as_attachment=True)


if __name__ == '__main__':
    app.debug=True
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # max size 16MB
    app.run()
