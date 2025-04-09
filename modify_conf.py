import requests


def strip_outer_parentheses(s):
    """去掉最外层的一对括号（如果存在）"""
    s = s.strip()
    if s.startswith('(') and s.endswith(')'):
        # 确保是配对的括号
        count = 0
        for i, char in enumerate(s):
            if char == '(':
                count += 1
            elif char == ')':
                count -= 1
            if count == 0 and i != len(s) - 1:
                # 中间就闭合了，不是包裹整个字符串的括号
                return s
        return s[1:-1]
    return s


def get_node_group(text):
    lines = text.strip().splitlines()
    converted = []
    startflag = False
    for line in lines:
        if startflag:
            if not line.startswith("custom_proxy_group="):
                continue

            # 去掉前缀
            content = line[len("custom_proxy_group="):]
            parts = content.split('`')
            name = parts[0].strip()
            type_ = parts[1].strip()

            if type_ == "select":
                #regex = parts[2].strip() if len(parts) > 2 else "*"
                regex = parts[2].strip() if len(parts) > 2 and (parts[2] != '.*') else "*"
                regex = strip_outer_parentheses(regex)
                converted_line = f"{name} = select,policy-regex-filter={regex}"

            elif type_ == "url-test":
                regex = parts[2].strip() if len(parts) > 2 and (parts[2] != '.*') else "*"
                regex = strip_outer_parentheses(regex)
                url = parts[3].strip() if len(parts) > 3 else "http://www.gstatic.com/generate_204"

                interval = "180"
                timeout = "5"
                tolerance = "100"
                if len(parts) > 4:
                    nums = parts[4].split(',')
                    if len(nums) == 3:
                        interval, timeout, tolerance = nums[0], nums[1], nums[2]

                converted_line = (
                    f"{name} = url-test,"
                    f"interval={interval},tolerance={tolerance},timeout={timeout},"
                    f"url={url},policy-regex-filter={regex}"
                )
            else:
                continue

            converted.append(converted_line)
        else:
            pass
            #converted.append(line)

        if not '3、节点组' in line:
            continue
        else:
            startflag = True

    return '\n'.join(converted)


def get_strategy_group(input_text):
    output_lines = []

    for line in input_text.splitlines():
        if '3、节点组' in line:
            break
        line = line.strip()
        if line.startswith("custom_proxy_group="):
            # 处理一行代理组
            try:
                left, right = line.split("=", 1)
                name, rest = right.split("`", 1)
                group_type, *proxies = rest.split("`[]")

                # 修正 group_type 重复问题
                if group_type == "select":
                    result_line = f"{name} = select," + ",".join(proxies)
                elif group_type == "url-test":
                    # 获取最后的参数字符串（如 URL 和超时设置等）
                    if '`' in proxies[-1]:
                        last_proxy_part = proxies[-1]
                        proxies = proxies[:-1]
                        url_params = last_proxy_part.split('`')[-1]
                    else:
                        url_params = ""

                    proxy_name = name  # Shadowrocket 名称保持不变
                    result_line = f"{proxy_name} = url-test," + ",".join(proxies)
                    if url_params:
                        result_line += f",{url_params}"
                else:
                    result_line = f"{name} = {group_type}," + ",".join(proxies)

                output_lines.append(result_line)
            except Exception as e:
                print(f"处理行出错: {line}\n错误信息: {e}")
        else:
            pass
            #output_lines.append(line)
    return "\n".join(output_lines)


def get_github_config(url):
    # 发送 GET 请求
    response = requests.get(url)
    # 检查请求是否成功
    if response.status_code == 200:
        content = response.text
        print("请求成功：\n")
        return content
    else:
        print(f"请求失败，状态码：{response.status_code}")
        return -1


def get_url_group(input_text):
    output_lines = []
    for line in input_text.splitlines():
        line = line.strip()
        if line.startswith("ruleset"):
            parts = line.split(',')
            name = parts[0].split('=')[1].strip()
            url = parts[1].strip()
            # 只处理URL不为空的情况
            if url and url != '[]FINAL':
                output_lines.append(f"RULE-SET,{url},{name}")
            else:
                output_lines.append('FINAL,{}'.format(name))
        else:
            pass
            #output_lines.append(line)
    return "\n".join(output_lines)


def modify_shadowrocket_conf(input_path, output_path, node_group, strategy_group, url_group):
    with open(input_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    section_indices = {
        'Proxy Group': None,
        'Rule': None,
        'Host': None,
    }

    # 定位各个 section 的开始行
    for i, line in enumerate(lines):
        if line.strip() == '[Proxy Group]':
            section_indices['Proxy Group'] = i
        elif line.strip() == '[Rule]':
            section_indices['Rule'] = i
        elif line.strip() == '[Host]':
            section_indices['Host'] = i

    if None in section_indices.values():
        raise ValueError("配置文件中缺少必要的段落：[Proxy Group]、[Rule] 或 [Host]")

    # 保留注释行并插入 a 和 b 到 [Proxy Group] 后
    proxy_group_start = section_indices['Proxy Group'] + 1
    rule_start = section_indices['Rule']
    proxy_group_lines = [
        line for line in lines[proxy_group_start:rule_start]
        if line.strip().startswith('#') or line.strip() == ''
    ]
    proxy_group_lines += [node_group + '\n', strategy_group + '\n']

    # 插入 c 到 [Rule] 段后，直到 [Host]
    rule_lines = [url_group + '\n']

    # 重建内容
    modified_lines = (
        lines[:proxy_group_start] +
        proxy_group_lines +
        lines[rule_start:rule_start + 1] +
        rule_lines +
        lines[section_indices['Host']:]
    )

    # 保存到新文件
    with open(output_path, 'w', encoding='utf-8') as f:
        f.writelines(modified_lines)

def download_ini_and_modify(input_path, output_path):
    url = 'https://gh-proxy.com/raw.githubusercontent.com/startrace111/clash/refs/heads/main/Cash-All.ini'
    githubconf = get_github_config(url)
    node_group = get_node_group(githubconf)
    url_group = get_url_group(githubconf)
    strategy_group = get_strategy_group(githubconf)
    # input_path = '/Users/zhuanjie/fuckGFW/ChatGPT京东emby迅雷old3.conf'
    # output_path = '/Users/zhuanjie/fuckGFW/ChatGPT京东emby迅雷convert.conf'
    modify_shadowrocket_conf(input_path, output_path, node_group, strategy_group, url_group)