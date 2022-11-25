import json
import os
import os.path

from argparse import ArgumentParser

def main():
    # Argument 처리
    parser = ArgumentParser(description = 'Process NIA_PET Add BoundingBox')
    parser.add_argument('SrcPath', type=str, nargs=1) #입력경로
    parser.add_argument('DstPath', type=str, nargs=1) #목적경로
    args = parser.parse_args()

    if not os.path.isdir(args.SrcPath[0]): #리스트형태이므로 [0]으로 꺼내어 str으로 해당 변수가 참조가능하도록 하며 해당 path가 폴더가 아닌 경우
      print("ERROR> Invalid path") # 앞과 같은 에러를 
      return #main함수의 실행결과로 보내고 종료함
    
    srcPath = args.SrcPath[0] #마찬가지로 str형태의 cmd 혹은 powershell 혹은 또 다른 지정을 받은 값의 경로를 입력경로로 저장 
    dstPath = args.DstPath[0] #마찬가지로 str형태의 cmd 혹은 powershell 혹은 또 다른 지정을 받은 값의 경로를 목적경로로 저장
 
        #목적경로 폴더 생성
    for (root, dirs, files) in os.walk(srcPath): #root 최상위 폴더 dirs 하위폴더 files 파일 하위 폴더가 없을때까지 가장 말단 폴더까지 dirs -> srcPath로 재귀함수로 탐색
        # 통계용 리스트(딕셔너리형태로 생성) for문 안에 넣어 통계가 디렉토리별로 생성됨
        breed_count = {}
        age_count = {}
        species_count = {}
        region_count = {}
        subdir_name = ""
        #지역, 종류, 문자등 초기화 initialization
        output_target_path = dstPath
        if srcPath != root: #최상위 폴더가 아닌 경우(재귀단계) test data에서의 input이 아닌 Class A와 Class B
            subdir_name = root.replace(srcPath, "") #root가 Class A일 경우 root 앞의 경로인 input을 지워서 지정할 폴더명을 가져옴
            output_target_path = dstPath + subdir_name #output폴더 내부에 지정하기위한 폴더명의 path를 정의
            if not os.path.exists(output_target_path): #정의된 path가 존재하지않으면 폴더를 생성
                os.makedirs(output_target_path)   
            try:
                if len(files) > 0: #폴더내부에 파일이 존재하면
                    for filename in files: #각각의 파일들에 대하여
                        name, ext = os.path.splitext(filename)#이름과 확장자를 받아서
                        if ext.lower() == '.json': #대소문자를 소문자로 정규화시켜서 json파일인지 확인하고 맞다면
                            jsonPath = os.path.join(root, filename) #파일이름과 root(path)와 합쳐서 json파일의 경로를 정의 
                            newJsonPath = os.path.join(output_target_path, name) #새로 생성될 json의 path를 저장
                            breed_count, age_count, species_count, region_count = saveJson(jsonPath, newJsonPath, breed_count, age_count, species_count, region_count)
                            #위에 해당하는 각 attribute를 아래에 정의한 saveJson함수 내부 정보복제, 바운딩박스 추가 및 통계count 누적형으로 받으며 폴더가 바뀔경우 초기화
            except Exception as e:
                break
            
            finally: 
                with open(output_target_path + os.sep + "{}_count.txt".format(subdir_name), "w", encoding="UTF-8") as countfile: 
                    #각 폴더의 통계를 _count.txt형태로 저장 os.sep OS 에 따라 \ 나 / 가 반환
                    countfile.write(f"BREED: {breed_count}\n")
                    countfile.write(f"AGE: {age_count}\n")
                    countfile.write(f"SPECIES: {species_count}\n")
                    countfile.write(f"REGION: {region_count}\n")
                    

#BoundingBodx 추가 후 json 저장
def saveJson(jsonPath, newJsonPath, breed_count, age_count, species_count, region_count):
    with open(jsonPath, "r", encoding="UTF-8") as json_file: #jsonpath에 해당하는 json파일을 열어서<_io.TextIOWrapper name='./input\\Class A\\IMG_D_A3_01_000010.json' mode='r' encoding='UTF-8'> json_file로 정의하고
        dictionary = json.load(json_file) #json_file을 읽어오고 dictionary에 정의

    try:
        len_label = len(dictionary['labelingInfo']) #labelingInfo의 갯 수 여기선 폴리곤의 갯 수
        metaData = {} #메타데이터를 담을 딕셔너리 정의
        metaData['metaData'] = dictionary['metaData']#metaData
        metaData['inspRejectYn'] = dictionary['inspRejectYn']
        metaData['labelingInfo'] = []
    except Exception as e:
        print(jsonPath + " jsonError") # josnpath가 없거나 잘못된 경우 예외처리
        raise e
    
    #통계 데이터 추가
    breed = metaData['metaData']['breed']#metadata안 breed의 value를 breed에 정의
    if breed not in breed_count: # breed안에 없다면 key : breed value : 1 else 1을 추가
        breed_count[breed] = 1
    else:
        breed_count[breed] += 1

    age = metaData['metaData']['age']
    if age not in age_count:
        age_count[age] = 1
    else:
        age_count[age] += 1
    
    species = metaData['metaData']['species']
    if species not in species_count:
        species_count[species] = 1
    else:
        species_count[species] += 1

    region = metaData['metaData']['region']
    if region not in region_count:
        region_count[region] = 1
    else:
        region_count[region] += 1

    for index in range(len_label): #폴리곤을 순차적으로 불러오고
        try:
            poly = dictionary['labelingInfo'][index]['polygon']['location'][0] #폴리곤 포인트의 좌표값들을 poly에 정의하고
            len_poly = len(poly) // 2 + 1 #좌표의 갯수를 2로 나눔 각 좌표에는 x, y좌표가 있으므로 + 1은? 좌표가 x0이 아닌 x1부터 시작
        except Exception as e:
            print(jsonPath + " jsonError") # josnpath가 잘못된 경우 예외처리
            raise e

        y_list = []
        x_list = []

        for i in range(1, len_poly):
            y_value = dictionary['labelingInfo'][index]['polygon']['location'][0]['y{0}'.format(i)] #dictionary의 index에 해당하는 좌표값을 y_value에 정의 labelinginfo는 list
            x_value = dictionary['labelingInfo'][index]['polygon']['location'][0]['x{0}'.format(i)]
            y_list.append(int(y_value))#각 좌표값을 숫자형태로 추가
            x_list.append(int(x_value))
        
        Xmin = min(x_list) #x리스트에서 가장 작은숫자를 정의
        Xmax = max(x_list) #x리스트에서 가장 큰 숫자를 정의
        Ymin = min(y_list)
        Ymax = max(y_list)

        polygon = dictionary['labelingInfo'][index]['polygon'] #input의 폴리곤의 색상, 위치, 라벨, 타입을 polygon에정의하고
        metaData['labelingInfo'].append({'polygon' : polygon}) #output할 metaData 라벨링인포에 폴리곤을 추가
        AddData = metaData['labelingInfo'][index] #폴리곤정보를 AddData에 정의

        #기존의 json 파일에 boundingbox가 있는 경우
        if 'boundingBox' in dictionary['labelingInfo'][index].keys():
            boundingbox = dictionary['labelingInfo'][index]['boundingBox']
            metaData['labelingInfo'][index]['boundingBox'] = boundingbox
            
        else: #바운딩박스 추가
            location = {"location": [{"Xmin": Xmin ,"Ymin" : Ymin, "Xmax" : Xmax, "Ymax" : Ymax}]}
            AddData['boundingBox'] = location 
     
        #바운딩박스의 라벨정보와 타입을 정의
        AddData['boundingBox']['label'] = dictionary['labelingInfo'][index]['polygon']['label']
        AddData['boundingBox']['type'] = "box"

        #추가 데이터가 있는 경우 
        """ 
        metaData['BasicInfo'] = {}
        metaData['BasicInfo']["identifier"] = "피부질환"
        metaData['BasicInfo']["src_path"] = 경로
        metaData['BasicInfo']["lable_path"] = 경로
        metaData['BasicInfo']["type"] = "json"
        metaData['BasicInfo']["fileformat"] = "jpg"
        """ 

    with open(newJsonPath + ".json", "w", encoding="UTF-8") as outfile: #json을 열어
        outfile.write(json.dumps(metaData, indent=3, ensure_ascii=False))
        #python 객체를 json 파일로 변환 indent=2는 계층을 설정 보기좋게 정리, 한글깨짐의 경우, "ensure_ascii = False"를 추가 

    return breed_count, age_count, species_count, region_count

if __name__ == "__main__":
    main()
