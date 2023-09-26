package main

import (
	"bufio"
	"encoding/json"
	"fmt"
	"log"
	"os"
	"regexp"
	"strconv"
	"strings"
)

type Tuple struct {
	key   string
	value string
}

type Report struct {
	balance  []Tuple
	profit   []Tuple
	cashflow []Tuple

	last_balance  []Tuple
	last_profit   []Tuple
	last_cashflow []Tuple
}

type RawRecord struct {
	TType  string          `json:"type"`
	Inside json.RawMessage `json:"inside"`
}

type Record struct {
	TType      string
	Inside     string
	InsideList []string
}

var balanceTablesKeywords = []string{"合并资产负债表", "资产负债表", "合并及母公司资产负债表", "合并及银行资产负债表"}
var profitTablesKeywords = []string{"合并利润表", "利润表", "合并及母公司利润表", "合并及银行利润表"}
var cashflowTablesKeywords = []string{"合并现金流量表", "现金流量表", "合并及母公司现金流量表", "合并及银行现金流量表"}
var importantTables = append(append(balanceTablesKeywords, profitTablesKeywords...), cashflowTablesKeywords...)
var importantTablesRegex = regexp.MustCompile("(?:" + strings.Join(importantTables, "|") + ")+$")

func judgeCaibaoTitle(line string) bool {
	pattern := regexp.MustCompile("(第[一二三四五六七八九十]+节)|(（[一二三四五六七八九十]+）)|\\([一二三四五六七八九十]+\\)|([一二三四五六七八九十]+、)|(\\d+、)|(（\\d+）)|\\(\\d+\\)")
	matches := pattern.FindAllStringSubmatch(line, -1)

	var matchedSubstrings []string
	for _, match := range matches {
		for _, group := range match {
			if group != "" {
				matchedSubstrings = append(matchedSubstrings, group)
			}
		}
	}

	return (len(matchedSubstrings) > 0 && strings.HasSuffix(line, "财务报表")) || (strings.HasSuffix(line, "财务报表") && len(line) < 10)
}

func removeTitleType(line string) string {
	pattern := regexp.MustCompile("^(第[一二三四五六七八九十]+节|（[一二三四五六七八九十]+）|\\([一二三四五六七八九十]+\\)|[一二三四五六七八九十]+、|\\d+、|（\\d+）|\\(\\d+\\)|\\d.)")
	result := pattern.ReplaceAllString(line, "")
	result = regexp.MustCompile(`[\(（][^)）]*[\)）]`).ReplaceAllString(result, "")
	return strings.Trim(result, " 、.\n\t")
}

func judgeTable(tagContent string) string {
	tagContent = strings.TrimSpace(tagContent)

	if judgeCaibaoTitle(tagContent) {
		return "caibao_title"
	}

	tagContent = removeTitleType(tagContent)
	if contains(balanceTablesKeywords, tagContent) || strings.HasSuffix(tagContent, "合并资产负债表") && len(tagContent) <= 10 {
		return "balance"
	} else if contains(profitTablesKeywords, tagContent) || strings.HasSuffix(tagContent, "合并利润表") && len(tagContent) > 0 {
		return "profit"
	} else if contains(cashflowTablesKeywords, tagContent) || strings.HasSuffix(tagContent, "合并现金流量表") && len(tagContent) > 0 {
		return "cashflow"
	}
	return ""
}

func judgeTableIsTrue(post_recordList []Record) bool {
	for i := 0; i < len(post_recordList); i++ {
		if post_recordList[i].TType == "excel" {
			return true
		}
	}
	return false
}

// Helper function to check if a string is in a slice
func contains(slice []string, val string) bool {
	for _, item := range slice {
		if item == val {
			return true
		}
	}
	return false
}

func extract(recordList []Record) Report {
	conditionFlag := 0
	var report Report
	balance := []Tuple{}
	profit := []Tuple{}
	cashflow := []Tuple{}

	last_balance := []Tuple{}
	last_profit := []Tuple{}
	last_cashflow := []Tuple{}

	//状态1，进入财务报表
	//状态2：找到合并资产负债表
	//状态3：退出合并资产负债表，找寻合并利润表
	//状态4：找到合并利润表 -> 2 3状态都可以直接转移到4
	//状态5：退出合并利润表，找寻合并现金流量表
	//状态6：找到合并现金流量表 -> 4 5 状态都可以直接转移到6
	for i := 0; i < len(recordList); i++ {
		record := recordList[i]
		// if record.TType == "text" && record.Inside == "合并资产负债表（更正后）" {
		// 	fmt.Println(11111)
		// }
		// if record.TType == "excel" && record.InsideList[0] == "合并股东权益变动表" {
		// 	fmt.Println(22222)
		// }
		// 修补
		match := importantTablesRegex.FindString(record.Inside)
		if match != "" && record.TType == "text" && strings.Contains(record.Inside, "负责人") {
			record.Inside = match
		}
		if conditionFlag == 0 && judgeTableIsTrue(recordList[i+1:i+7]) && (record.TType == "text" && judgeTable(record.Inside) == "balance" || (record.TType == "excel" && len(record.InsideList) > 0 && (record.InsideList[0]) == "balance")) {
			conditionFlag = 2
		} else if conditionFlag == 2 && judgeTableIsTrue(recordList[i+1:i+7]) && record.TType == "excel" && len(record.InsideList) > 0 && judgeTable(record.InsideList[0]) == "profit" {
			conditionFlag = 4
		} else if conditionFlag == 2 && record.TType == "excel" {
			s := record.InsideList
			// if len(balance) > 0 && strings.Contains(balance[len(balance)-1].key, "负债和所有者权益") {
			// 	continue
			// }
			if len(s) == 2 {
				balance = append(balance, Tuple{s[0], s[1]})
			} else if len(s) == 3 {
				balance = append(balance, Tuple{s[0], s[1]})
				last_balance = append(last_balance, Tuple{s[0], s[2]})
			} else if len(s) == 4 {
				balance = append(balance, Tuple{s[0], s[2]})
				last_balance = append(last_balance, Tuple{s[0], s[3]})
			} else if len(s) == 5 {
				balance = append(balance, Tuple{s[0], s[2]})
				last_balance = append(last_balance, Tuple{s[0], s[3]})
			} else if len(s) == 6 {
				balance = append(balance, Tuple{s[0], s[2]})
				last_balance = append(last_balance, Tuple{s[0], s[3]})
			}
		} else if conditionFlag == 2 && (record.TType == "text" && strings.HasSuffix(record.Inside, "母公司资产负债表") || conditionFlag == 2 && record.TType == "excel" && strings.HasSuffix(record.InsideList[0], "母公司资产负债表")) {
			conditionFlag = 3
		} else if (conditionFlag == 2 || conditionFlag == 3) && judgeTableIsTrue(recordList[i+1:i+7]) && (record.TType == "text" && judgeTable(record.Inside) == "profit" || record.TType == "excel" && len(record.InsideList) > 0 && judgeTable(record.InsideList[0]) == "profit") {
			conditionFlag = 4
		} else if (conditionFlag == 4 || conditionFlag == 5) && judgeTableIsTrue(recordList[i+1:i+7]) && (record.TType == "text" && judgeTable(record.Inside) == "cashflow") || (record.TType == "excel" && len(record.InsideList) > 0 && judgeTable(record.InsideList[0]) == "cashflow") {
			conditionFlag = 6
		} else if conditionFlag == 4 && record.TType == "excel" {
			// if len(profit) > 0 && strings.Contains(profit[len(profit)-1].key, "稀释每股收益") {
			// 	continue
			// }
			s := record.InsideList
			if len(s) == 2 {
				profit = append(profit, Tuple{s[0], s[1]})
			} else if len(s) == 3 {
				profit = append(profit, Tuple{s[0], s[1]})
				last_profit = append(last_profit, Tuple{s[0], s[2]})
			} else if len(s) == 4 {
				profit = append(profit, Tuple{s[0], s[2]})
				last_profit = append(last_profit, Tuple{s[0], s[3]})
			} else if len(s) == 5 {
				profit = append(profit, Tuple{s[0], s[2]})
				last_profit = append(last_profit, Tuple{s[0], s[3]})
			} else if len(s) == 6 {
				profit = append(profit, Tuple{s[0], s[2]})
				last_profit = append(last_profit, Tuple{s[0], s[3]})
			}
		} else if (conditionFlag == 4 && record.TType == "text" && strings.HasSuffix(record.Inside, "母公司利润表")) || (conditionFlag == 4 && record.TType == "excel" && len(record.InsideList) > 0 && strings.HasSuffix(record.InsideList[0], "母公司利润表")) {
			conditionFlag = 5
		} else if (conditionFlag == 4 || conditionFlag == 5) && judgeTableIsTrue(recordList[i+1:i+7]) && (record.TType == "text" && judgeTable(record.Inside) == "cashflow") || (record.TType == "excel" && len(record.InsideList) > 0 && judgeTable(record.InsideList[0]) == "cashflow") {
			conditionFlag = 6
		} else if conditionFlag == 6 && (record.TType == "text" && (strings.HasSuffix(record.Inside, "母公司现金流量表") || strings.HasSuffix(record.Inside, "合并所有者权益变动表") || strings.HasSuffix(record.Inside, "合并股东权益变动表"))) ||
			(record.TType == "excel" && len(record.InsideList) > 0 && (strings.HasSuffix(record.InsideList[0], "母公司现金流量表") || strings.HasSuffix(record.InsideList[0], "合并所有者权益变动表") || strings.HasSuffix(record.InsideList[0], "合并股东权益变动表"))) {
			break
		} else if conditionFlag == 6 && record.TType == "excel" {
			// if len(cashflow) > 0 && strings.Contains(cashflow[len(cashflow)-1].key, "期末现金及现金等价物余额") {
			// 	continue
			// }
			s := record.InsideList
			if len(s) == 2 {
				cashflow = append(cashflow, Tuple{s[0], s[1]})
			} else if len(s) == 3 {
				cashflow = append(cashflow, Tuple{s[0], s[1]})
				last_cashflow = append(last_cashflow, Tuple{s[0], s[2]})
			} else if len(s) == 4 {
				cashflow = append(cashflow, Tuple{s[0], s[2]})
				last_cashflow = append(last_cashflow, Tuple{s[0], s[3]})
			} else if len(s) == 5 {
				cashflow = append(cashflow, Tuple{s[0], s[2]})
				last_cashflow = append(last_cashflow, Tuple{s[0], s[3]})
			} else if len(s) == 6 {
				cashflow = append(cashflow, Tuple{s[0], s[2]})
				last_cashflow = append(last_cashflow, Tuple{s[0], s[3]})
			}
			if len(s) > 0 && strings.Contains(s[0], "期末现金及现金等价物余额") {
				break
			}
		}
	}
	report.balance = balance
	report.cashflow = cashflow
	report.profit = profit
	report.last_balance = last_balance
	report.last_cashflow = last_cashflow
	report.last_profit = last_profit
	return report
}

func get_all_report(filepath string, dir_out string) {
	separator := string(os.PathSeparator)
	filePreName := strings.Split(filepath, separator)[len(strings.Split(filepath, separator))-1]
	balanceFileName := dir_out + filePreName + "_balance.txt"
	profitFileName := dir_out + filePreName + "_profit.txt"
	cashflowFileName := dir_out + filePreName + "_cashflow.txt"

	file, err := os.Open(filepath)
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
	report := extract(recordList)

	balanceFile, _ := os.Create(balanceFileName)
	defer balanceFile.Close()

	balanceWriter := bufio.NewWriter(balanceFile)

	for _, t := range report.balance {
		fmt.Fprintln(balanceWriter, strings.ReplaceAll(t.key, "\n", "")+"\001"+strings.ReplaceAll(t.value, "\n", ""))
	}

	balanceWriter.Flush()

	profitFile, _ := os.Create(profitFileName)
	defer profitFile.Close()

	profitWriter := bufio.NewWriter(profitFile)

	for _, t := range report.profit {
		fmt.Fprintln(profitWriter, strings.ReplaceAll(t.key, "\n", "")+"\001"+strings.ReplaceAll(t.value, "\n", ""))
	}

	profitWriter.Flush()

	cashflowFile, _ := os.Create(cashflowFileName)
	defer cashflowFile.Close()

	cashflowWriter := bufio.NewWriter(cashflowFile)

	for _, t := range report.cashflow {
		fmt.Fprintln(cashflowWriter, strings.ReplaceAll(t.key, "\n", "")+"\001"+strings.ReplaceAll(t.value, "\n", ""))
	}

	cashflowWriter.Flush()

	if err := scanner.Err(); err != nil {
		log.Fatal(err)
	}

}

func main() {
	print(1)
	all_path := os.Args[1]
	dir_in := os.Args[2]
	dir_out := os.Args[3]
	process_num_str := os.Args[4]
	process_num, err := strconv.Atoi(process_num_str)
	process_id_str := os.Args[5]
	process_id, err := strconv.Atoi(process_id_str)

	// all_path := "output.txt"
	// dir_in := "E:\\alltxt\\"

	file, err := os.Open(all_path)
	if err != nil {
		log.Fatalf("failed to open file: %s", err)
	}

	scanner := bufio.NewScanner(file)
	scanner.Split(bufio.ScanLines)
	var txtlines []string

	for scanner.Scan() {
		txtlines = append(txtlines, scanner.Text())
	}

	file.Close()

	for i, eachline := range txtlines {
		if i%process_num != process_id {
			continue
		}
		file_name := strings.ReplaceAll(eachline, ".pdf", ".txt")
		println(i, file_name)
		// if file_name != "2022-11-24__青海华鼎实业股份有限公司__600243__青海华鼎__2021年__年度报告.txt" {
		// 	continue
		// }
		get_all_report(dir_in+file_name, dir_out)
	}

}
