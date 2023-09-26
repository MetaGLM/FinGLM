package main

import (
	"bufio"
	"encoding/json"
	"fmt"
	"log"
	"math"
	"os"
	"strconv"
	"strings"
)

type RawRecord struct {
	TType  string          `json:"type"`
	Inside json.RawMessage `json:"inside"`
}

type Record struct {
	TType      string
	Inside     string
	InsideList []string
}

type Tuple struct {
	Key   string
	Value string
}

func main() {
	listfile := os.Args[1]
	// 官方txt文件输入位置,末尾需要有\\
	var dir1 string = os.Args[2]
	// 输出文件
	var dir2 string = os.Args[3]
	ofile, _ := os.Open(listfile) // 请替换为你的文件名
	scanner := bufio.NewScanner(ofile)
	scanner.Split(bufio.ScanLines)
	var txtlines []string

	for scanner.Scan() {
		txtlines = append(txtlines, scanner.Text())
	}

	ofile.Close()

	resultFile, _ := os.Create(dir2 + "people.csv")
	defer resultFile.Close()
	writer := bufio.NewWriter(resultFile)

	for i, eachline := range txtlines {
		// if eachline != "2020-04-24__深圳市科信通信技术股份有限公司__300565__科信技术__2019年__年度报告.pdf" {
		// 	continue
		// }
		println(i, eachline)
		filePath := strings.ReplaceAll((dir1 + eachline), ".pdf", ".txt")
		file, err := os.Open(filePath)
		if err != nil {
			log.Fatal(err)
		}
		defer file.Close()

		recordList := []Record{}

		scanner := bufio.NewScanner(file)
		for scanner.Scan() {
			var rawRecord RawRecord
			var record Record
			err := json.Unmarshal([]byte(scanner.Text()), &rawRecord)
			if err != nil {
				log.Fatal(err)
			}
			if rawRecord.TType == "页眉" || rawRecord.TType == "页脚" {
				continue
			}
			record.TType = rawRecord.TType
			// 检查 Inside 字段是字符串还是列表
			// fmt.Println(string(rawRecord.Inside))
			s := string(rawRecord.Inside)
			if len(s) == 0 {
				continue
			}
			if s[1] == '[' {
				// 是列表
				insideList := []string{}
				a := s
				a, _ = strings.CutPrefix(a, "\"")
				a, _ = strings.CutSuffix(a, "\"")
				a = strings.ReplaceAll(a, "'", "\"")
				err = json.Unmarshal([]byte(a), &insideList)
				if err != nil {
					var insideString string
					err = json.Unmarshal(rawRecord.Inside, &insideString)
					if err != nil {
						log.Fatal(err)
					}
					record.Inside = insideString
				}
				record.InsideList = insideList
			} else {
				// 是字符串
				var insideString string
				err = json.Unmarshal(rawRecord.Inside, &insideString)
				if err != nil {
					log.Fatal(err)
				}
				record.Inside = insideString
			}
			recordList = append(recordList, record)
		}

		tupleList := []Tuple{}

		for _, r := range recordList {
			if r.TType == "excel" && len(r.InsideList) <= 5 && len(r.InsideList) >= 2 {
				the_str := r.InsideList[0]
				the_f := -1.00
				if (strings.Contains(the_str, "人员") || strings.Contains(the_str, "博士") || strings.Contains(the_str, "研究生") || strings.Contains(the_str, "员工") || strings.Contains(the_str, "硕士")) &&
					(!strings.Contains(the_str, "社保") && !strings.Contains(the_str, "工资") && !strings.Contains(the_str, "酬") && !strings.Contains(the_str, "金") && !strings.Contains(the_str, "付") &&
						!strings.Contains(the_str, "费") && !strings.Contains(the_str, "管") && !strings.Contains(the_str, "款") && !strings.Contains(the_str, "险") && !strings.Contains(the_str, "补")) {
					for _, v := range r.InsideList {
						v = strings.ReplaceAll(v, " ", "")
						v = strings.ReplaceAll(v, ",", "")
						v = strings.ReplaceAll(v, "，", "")
						v = strings.ReplaceAll(v, "%", "")
						f, err2 := strconv.ParseFloat(v, 64)
						if err2 != nil {
							continue
						} else {
							the_f = f
							break
						}
					}
				}
				if the_f != -1.00 {
					tupleList = append(tupleList, Tuple{the_str, fmt.Sprintf("%.2f", the_f)})
				}

				the_str_1 := r.InsideList[1]
				the_f_1 := -1.00
				if (strings.Contains(the_str_1, "人员") || strings.Contains(the_str_1, "博士") || strings.Contains(the_str_1, "研究生") || strings.Contains(the_str_1, "员工") || strings.Contains(the_str_1, "硕士")) &&
					(!strings.Contains(the_str_1, "社保") && !strings.Contains(the_str_1, "工资") && !strings.Contains(the_str_1, "酬") && !strings.Contains(the_str_1, "金") && !strings.Contains(the_str_1, "付") &&
						!strings.Contains(the_str_1, "费") && !strings.Contains(the_str_1, "管") && !strings.Contains(the_str_1, "款") && !strings.Contains(the_str_1, "险") && !strings.Contains(the_str_1, "补")) {
					for _, v := range r.InsideList {
						v = strings.ReplaceAll(v, " ", "")
						v = strings.ReplaceAll(v, ",", "")
						v = strings.ReplaceAll(v, "，", "")
						v = strings.ReplaceAll(v, "%", "")
						f, err2 := strconv.ParseFloat(v, 64)
						if err2 != nil {
							continue
						} else {
							the_f_1 = f
							break
						}
					}
				}
				if the_f_1 != -1.00 {
					tupleList = append(tupleList, Tuple{the_str_1, fmt.Sprintf("%.2f", the_f_1)})
				}
			}
		}
		// fmt.Println(tupleList)
		curMax := 0.0
		studyMan := "0"
		studyManRatio := "0.00"
		masterMan := "0"
		masterManOver := "0"
		phdMan := "0"
		phdManOver := "0"
		shengchanMan := "0"
		xiaoshouMan := "0"
		jishuMan := "0"
		caiwuMan := "0"
		xingzhengMan := "0"
		for _, t := range tupleList {
			s := t.Key
			s2 := t.Value
			s3 := strings.Split(t.Value, ".")[0]
			i, _ := strconv.ParseFloat(s2, 64)

			if i < 300000 && i > curMax && strings.Contains(s, "数") && i == math.Floor(i) {
				curMax = i
			}
			if strings.Contains(s, "研发") && !strings.Contains(s, "比") {
				if i < 10000 {
					studyMan = s3
				}
			} else if (strings.Contains(s, "开发")) && (!strings.Contains(s, "比")) {
				if i < 100000 && studyMan == "0" {
					studyMan = s3
				}
			} else if (strings.Contains(s, "研发") || strings.Contains(s, "开发")) && (strings.Contains(s, "比")) {
				studyManRatio = s2
			} else if (strings.Contains(s, "硕士") || strings.Contains(s, "研究生")) && !strings.Contains(s, "以上") {
				if i < 100000 {
					masterMan = s3
				}
			} else if (strings.Contains(s, "硕士") || strings.Contains(s, "研究生")) && strings.Contains(s, "以上") {
				if i < 100000 {
					masterManOver = s3
				}
			} else if (strings.Contains(s, "博士")) && !strings.Contains(s, "以上") {
				if i < 2000 {
					phdMan = s3
				}
			} else if (strings.Contains(s, "博士")) && strings.Contains(s, "以上") {
				if i < 2000 {
					phdManOver = s3
				}
			} else if strings.Contains(s, "生产") {
				shengchanMan = s3
			} else if strings.Contains(s, "销售") {
				xiaoshouMan = s3
			} else if strings.Contains(s, "技术") {
				jishuMan = s3
			} else if strings.Contains(s, "财务") {
				caiwuMan = s3
			} else if strings.Contains(s, "行政") {
				xingzhengMan = s3
			}
		}
		// fmt.Print(shengchanMan, xiaoshouMan, jishuMan, caiwuMan, xingzhengMan)
		total := fmt.Sprintf("%.0f", curMax)
		// fmt.Println("总人数" + total)
		// fmt.Println("研发人员" + studyMan)
		if studyManRatio == "0.00" && total != "0" {
			a, _ := strconv.ParseFloat(studyMan, 64)
			b, _ := strconv.ParseFloat(total, 64)
			studyManRatio = fmt.Sprintf("%.2f", a*100/b)
		}
		// fmt.Println("研发人员比率" + studyManRatio)
		// fmt.Println("硕士人数" + masterMan)
		if masterManOver == "0" && masterMan != "0" {
			if phdMan != "0" {
				a, _ := strconv.ParseFloat(masterMan, 64)
				b, _ := strconv.ParseFloat(phdMan, 64)
				masterManOver = fmt.Sprintf("%.0f", a+b)
			} else if phdManOver != "0" {
				a, _ := strconv.ParseFloat(masterMan, 64)
				b, _ := strconv.ParseFloat(phdManOver, 64)
				masterManOver = fmt.Sprintf("%.0f", a+b)
			} else {
				masterManOver = masterMan
			}
		}
		// fmt.Println("硕士以上人数" + masterManOver)
		// fmt.Println("博士人数" + phdMan)
		if phdManOver == "0" && phdMan != "0" {
			phdManOver = phdMan
		}
		// fmt.Println("博士以上人数" + phdManOver)

		result := []string{}
		result = append(result, total)
		result = append(result, studyMan)
		result = append(result, studyManRatio)
		result = append(result, masterMan)
		result = append(result, masterManOver)
		result = append(result, phdMan)
		result = append(result, phdManOver)
		result = append(result, shengchanMan)
		result = append(result, xiaoshouMan)
		result = append(result, jishuMan)
		result = append(result, caiwuMan)
		result = append(result, xingzhengMan)

		year := strings.Split(eachline, "__")[4]
		src := strings.Split(eachline, "__")[5]
		code := strings.Split(eachline, "__")[2]
		bondname := strings.Split(eachline, "__")[3]
		resultStr := strings.Join(result, "\001")
		line := fmt.Sprintf("%s\001%s\001%s\001%s\001%s", year, src, code, bondname, resultStr)
		fmt.Fprintln(writer, line)
		writer.Flush()

	}

}
