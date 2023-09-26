package main

import (
	"bufio"
	"encoding/json"
	"fmt"
	"log"
	"os"
	"regexp"
	"strings"
	"unicode/utf8"
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
	// 记得改回来
	listfile := os.Args[1]
	// 官方txt文件输入位置,末尾需要有\\
	var dir1 string = os.Args[2]
	// 输出文件
	var dir2 string = os.Args[3]

	// listfile := "E:\\all_path.txt"
	// var dir1 string = "E:\\alltxt\\"
	// var dir2 string = "E:\\combine_data\\"

	ofile, _ := os.Open(listfile)
	scanner := bufio.NewScanner(ofile)
	scanner.Split(bufio.ScanLines)
	var txtlines []string

	for scanner.Scan() {
		txtlines = append(txtlines, scanner.Text())
	}

	ofile.Close()

	resultFile, _ := os.Create(dir2 + "baseinfo.csv")
	defer resultFile.Close()
	writer := bufio.NewWriter(resultFile)

	for i, eachline := range txtlines {
		// if eachline != "2021-04-01__中芯国际集成电路制造有限公司__688981__中芯国际__2020年__年度报告.pdf" {
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

		// http://www.sse.com.cn

		count := 0
		work_address := ""
		registry_address := ""
		email := ""
		person := ""
		website := ""

		lianxi_start_pos := -1
		jiben_start_pos := -1
		for i, r := range recordList {
			if r.TType == "text" {
				if strings.Contains(r.Inside, "联系人和联系方式") {
					lianxi_start_pos = i
				}
				if strings.Contains(r.Inside, "基本情况简介") {
					jiben_start_pos = i
				}
			}
		}
		for i, r := range recordList {
			if work_address != "" && registry_address != "" && email != "" && person != "" {
				break
			}
			if r.TType == "excel" && len(r.InsideList) <= 6 && len(r.InsideList) >= 2 {
				the_str := r.InsideList[0]
				if strings.Contains(the_str, "办公") && strings.Contains(the_str, "地址") && work_address == "" && !strings.Contains(the_str, "会计") {
					count = 10
					for _, v := range r.InsideList[1:] {
						if (strings.Contains(v, "省") || strings.Contains(v, "市") || strings.Contains(v, "区") || strings.Contains(v, "城")) || utf8.RuneCountInString(v) >= 4 {
							work_address = strings.ReplaceAll(strings.Trim(v, " "), "\n", "")
							break
						}
					}
				} else if strings.Contains(the_str, "注册") && strings.Contains(the_str, "地址") && registry_address == "" {
					count = 10
					for _, v := range r.InsideList[1:] {
						if (strings.Contains(v, "省") || strings.Contains(v, "市") || strings.Contains(v, "区") || strings.Contains(v, "城")) || utf8.RuneCountInString(v) >= 4 {
							registry_address = strings.ReplaceAll(strings.Trim(v, " "), "\n", "")
							break
						}
					}
				} else if strings.Contains(the_str, "法定") && strings.Contains(the_str, "代") && person == "" {
					count = 10
					for i := 1; i < len(r.InsideList); i++ {
						v := r.InsideList[i]
						if len(v) <= 12 && len(v) >= 6 {
							person = strings.ReplaceAll(strings.Trim(v, " "), "\n", "")
							break
						}
					}
				} else if strings.Contains(the_str, "网址") {
					for i := 1; i < len(r.InsideList); i++ {
						v := r.InsideList[i]
						if (strings.Contains(v, "网址") || strings.Contains(v, "网站")) && website == "" {
							website = strings.ReplaceAll(strings.Trim(v, " "), "\n", "")
							website = replaceAllChinese(website)
							website = findWebSite(website)
							break
						}
					}
				}

				if count > 0 {
					if lianxi_start_pos != -1 && jiben_start_pos != -1 && i < jiben_start_pos && email == "" {
						continue
					}
					for _, v := range r.InsideList {
						if strings.Contains(v, "@") && email == "" {
							email = strings.ReplaceAll(strings.Trim(v, " "), "\n", "")
							email = replaceAllChinese(email)
							break
						}
					}
				}
				count--
			}

		}

		if work_address == "" || registry_address == "" {
			count := 0
			for i := 0; i < len(recordList)/3; i++ {
				r := recordList[i]
				if r.TType == "text" {
					if strings.Contains(r.Inside, "基本情况简介") || (strings.Contains(r.Inside, "公司信息") && utf8.RuneCountInString(r.Inside) <= 8) {
						count = 20
					}
				}
				if count > 0 {
					if strings.Contains(r.Inside, "注册地址") && registry_address == "" {
						registry_address = strings.ReplaceAll(strings.Trim(r.Inside, " "), "\n", "")
						registry_address = strings.Trim(registry_address, "注册地址")
					} else if strings.Contains(r.Inside, "办公地址") && work_address == "" {
						work_address = strings.ReplaceAll(strings.Trim(r.Inside, " "), "\n", "")
						work_address = strings.Trim(work_address, "办公地址")
					} else if strings.Contains(r.Inside, "法定代表人") && person == "" {
						person = strings.ReplaceAll(strings.ReplaceAll(strings.Trim(r.Inside, " "), "\n", ""), "法定代表人", "")
					} else if strings.Contains(r.Inside, "网址") && person == "" {
						website = strings.ReplaceAll(strings.Trim(r.Inside, " "), "\n", "")
						website = replaceAllChinese(website)
						website = findWebSite(website)
					} else if strings.Contains(r.Inside, "邮箱") || strings.Contains(r.Inside, "电子信箱") {
						email = strings.ReplaceAll(strings.Trim(r.Inside, " "), "\n", "")
						email = strings.Trim(email, "电子信箱")
						email = replaceAllChinese(email)
					}
				}
				count--
			}
		}

		if website == "" {
			flag := false
			for _, r := range recordList {
				if flag {
					break
				}
				if r.TType == "text" {
					s := findWebSite(r.Inside)
					if s != "" && !strings.Contains(s, "www.sse.com") && !strings.Contains(s, "cninfo") {
						website = s
						flag = true
					}
				} else if r.TType == "excel" {
					s := r.InsideList
					for _, v := range s {
						t := findWebSite(v)
						if t != "" && !strings.Contains(t, "www.sse.com") && !strings.Contains(t, "cninfo") {
							website = t
							flag = true
						}
					}
				}
			}
		}
		if website != "" {
			the_website := "https://" + website
			flag := false
			for _, r := range recordList {
				if flag {
					break
				}
				if r.TType == "text" {
					if strings.Contains(r.Inside, the_website) {
						website = the_website
						flag = true
					}
				} else if r.TType == "excel" {
					s := r.InsideList
					for _, v := range s {
						if strings.Contains(v, the_website) {
							website = the_website
							flag = true
						}
					}
				}
			}
		}

		if website != "" && !strings.HasPrefix(website, "http") {
			the_website := "http://" + website
			flag := false
			for _, r := range recordList {
				if flag {
					break
				}
				if r.TType == "text" {
					if strings.Contains(r.Inside, the_website) {
						website = the_website
						flag = true
					}
				} else if r.TType == "excel" {
					s := r.InsideList
					for _, v := range s {
						if strings.Contains(v, the_website) {
							website = the_website
							flag = true
						}
					}
				}
			}
		}

		result := []string{}
		result = append(result, work_address)
		result = append(result, registry_address)
		result = append(result, email)
		result = append(result, person)
		result = append(result, website)

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

func replaceAllChinese(text string) string {
	re := regexp.MustCompile("[\u4e00-\u9fa5]+")
	r := re.ReplaceAllString(text, "")
	return r
}

func findWebSite(text string) string {
	re := regexp.MustCompile(`[\w-]+(\.[\w-]+)+([\w.,@?^=%&:/~+#-]*[\w@?^=%&/~+#-])?`)
	urls := re.FindAllString(text, -1)
	if len(urls) == 1 {
		if (strings.Contains(urls[0], "www.") || strings.Contains(urls[0], "WWW.")) && strings.Count(urls[0], ".") >= 2 {
			s := strings.Split(urls[0], "/")
			if len(s) == 2 && strings.Trim(s[1], " ") == "" {
				return strings.Split(urls[0], "/")[0] + "/"
			} else {
				return strings.Split(urls[0], "/")[0]
			}
		} else {
			return ""
		}
	} else {
		return ""
	}
}
