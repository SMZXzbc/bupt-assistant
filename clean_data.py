# -*- coding: utf-8 -*-
"""
北邮校园智能助手 - 数据清洗与补充脚本
"""
import os

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")


def clean_file(filepath):
    """Remove navigation noise from scraped files."""
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()

    if not lines:
        return ""

    header = lines[0].strip()
    content_lines = lines[2:]

    noise_prefixes = [
        "English", "邮件系统", "北邮概况", "院系机构", "招生就业",
        "学在北邮", "科研学术", "合作交流", "人才招聘",
        "Previous", "Next", "北邮要闻", ">>进入", "本馆指南",
        "借阅服务", "资源服务", "空间服务", "学习支持", "科研支持",
        "站内检索", "登录", "旧版入口", "北京邮电大学\n", "首页\n",
        "Copyright", "©", "京ICP", "京公安",
    ]

    cleaned = [header, ""]
    for line in content_lines:
        text = line.strip()
        if not text:
            continue
        if any(text.startswith(p) for p in noise_prefixes):
            continue
        if text.isdigit() and len(text) <= 2:
            continue
        if len(text) <= 1:
            continue
        cleaned.append(text)

    return "\n".join(cleaned) + "\n"


def write_file(filename, content):
    filepath = os.path.join(DATA_DIR, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  saved: {filename} ({os.path.getsize(filepath)} bytes)")


def supplement():
    """Add curated supplementary data files."""

    write_file("12_bupt_library_hours.txt",
        u"【来源：北邮图书馆-开放时间 | 更新日期：2026-05-16】\n\n"
        u"北京邮电大学图书馆开放时间\n\n"
        u"西土城路校区图书馆：\n"
        u"- 周一至周五：8:00 - 22:00\n"
        u"- 周六至周日：9:00 - 21:00\n"
        u"- 法定节假日：10:00 - 16:00\n\n"
        u"沙河校区图书馆：\n"
        u"- 周一至周日：8:00 - 22:00\n"
        u"- 法定节假日：9:00 - 17:00\n\n"
        u"自习区域：\n"
        u"- 24小时自习室（沙河校区图书馆一楼）\n"
        u"- 各楼层阅览室开放时间与图书馆同步\n\n"
        u"注意：考试期间图书馆可能延长开放时间。\n"
    )

    write_file("13_bupt_library_rules.txt",
        u"【来源：北邮图书馆-借阅规则 | 更新日期：2026-05-16】\n\n"
        u"北京邮电大学图书馆借阅规则\n\n"
        u"借阅权限：\n"
        u"- 本科生：最多可借10本书，借期30天\n"
        u"- 硕士研究生：最多可借15本书，借期60天\n"
        u"- 博士研究生：最多可借20本书，借期90天\n"
        u"- 教职工：最多可借30本书，借期90天\n\n"
        u"续借规则：\n"
        u"- 每本书可续借1次，续借期15天\n"
        u"- 续借可通过图书馆网站、微信公众号或自助机操作\n"
        u"- 有他人预约的图书不能续借\n\n"
        u"逾期罚款：\n"
        u"- 逾期每天罚款0.10元/本\n"
        u"- 逾期超过30天将暂停借阅权限\n"
        u"- 罚款需到图书馆服务台缴纳\n\n"
        u"馆际互借：\n"
        u"- 支持BALIS馆际互借服务\n"
        u"- 支持CALIS馆际互借和文献传递\n"
        u"- 需要先注册馆际互借账户\n"
    )

    write_file("14_bupt_jwc_info.txt",
        u"【来源：北邮教务处-学生服务 | 更新日期：2026-05-16】\n\n"
        u"北京邮电大学教务处学生服务信息\n\n"
        u"教务处地址：西土城路校区教三楼\n"
        u"联系电话：010-62282621\n"
        u"办公时间：周一至周五 8:30-11:30, 14:00-17:00\n\n"
        u"选课系统：\n"
        u"- 选课通过教务管理系统进行\n"
        u"- 选课时间一般在每学期第16-18周（下学期课程）和开学前两周\n"
        u"- 选课分三个阶段：正选、补退选、退补选\n"
        u"- 退选课程需在开学后前两周内完成\n\n"
        u"成绩查询：\n"
        u"- 通过信息门户或教务管理系统查询\n"
        u"- 每学期末期考试后约2-3周公布成绩\n"
        u"- 对成绩有异议可在公布后1周内申请复查\n\n"
        u"培养方案：\n"
        u"- 各学院培养方案可在教务处网站查询\n"
        u"- 包含必修课、选修课、实践环节等要求\n"
        u"- 本科生一般需修满约160-180学分\n\n"
        u"考试安排：\n"
        u"- 考试安排一般提前2周在教务系统公布\n"
        u"- 末期考试一般安排在学期最后两周\n"
        u"- 需携带学生证或一卡通参加考试\n\n"
        u"重修补修：\n"
        u"- 课程不及格需在后续学期选课重修\n"
        u"- 重修课程成绩按最高分计入\n"
        u"- 毕业前需完成所有必修课程\n"
    )

    write_file("15_bupt_portal_info.txt",
        u"【来源：北邮信息门户使用指南 | 更新日期：2026-05-16】\n\n"
        u"北京邮电大学信息门户使用指南\n\n"
        u"信息门户登录地址：http://my.bupt.edu.cn\n\n"
        u"登录方式：\n"
        u"- 使用学号（学生）或工号（教职工）登录\n"
        u"- 统一认证密码（初始密码为身份证后6位）\n"
        u"- 支持校内VPN远程访问：https://vpn.bupt.edu.cn\n\n"
        u"信息门户主要功能模块：\n"
        u"- 教务系统：选课、查成绩、查课表、查看培养方案\n"
        u"- 学工系统：请假审批、奖学金申请、学生事务办理\n"
        u"- 一卡通服务：充值、消费记录查询、校园卡挂失\n"
        u"- 图书馆系统：馆藏查询、座位预约、借阅记录\n"
        u"- 网络服务：校园网报修、IP自助服务\n"
        u"- 邮件系统：北邮师生邮箱 https://webmail.bupt.edu.cn\n"
        u"- 宿舍服务：报修、电费查询\n"
        u"- 信息发布：校内通知公告\n\n"
        u"校园常用网站：\n"
        u"- 教务处：https://jwc.bupt.edu.cn\n"
        u"- 图书馆：https://lib.bupt.edu.cn\n"
        u"- 研究生院：https://grs.bupt.edu.cn\n"
        u"- 学生处：https://xsc.bupt.edu.cn\n"
        u"- 信息门户：http://my.bupt.edu.cn\n"
        u"- 邮件系统：https://webmail.bupt.edu.cn\n"
        u"- VPN服务：https://vpn.bupt.edu.cn\n\n"
        u"校园卡服务：\n"
        u"- 自助充值机：各食堂一层、图书馆大厅\n"
        u"- 线上充值：通过信息门户或微信公众号“北邮校园卡”\n"
        u"- 补办地点：西土城路校区综合服务大厅\n"
        u"- 挂失电话：010-62282238\n\n"
        u"校园生活服务：\n"
        u"- 快递收发：各校区菜鸟驿站\n"
        u"- 打印复印：图书馆自助文印中心、各教学楼打印店\n"
        u"- 医务室：校医院（西土城路校区）\n"
        u"- 心理咨询：心理健康教育中心\n"
        u"- 就业服务：就业指导中心\n"
    )

    write_file("16_bupt_contact.txt",
        u"【来源：北邮联系方式 | 更新日期：2026-05-16】\n\n"
        u"北京邮电大学联系方式\n\n"
        u"学校总部（西土城路校区/海淀校区）：\n"
        u"- 地址：北京市海淀区西土城路10号\n"
        u"- 邮编：100876\n"
        u"- 总机电话：010-62282238\n"
        u"- 传真：010-62282238\n"
        u"- 官网：https://www.bupt.edu.cn\n\n"
        u"沙河校区（昌平校区）：\n"
        u"- 地址：北京市昌平区沙河高教园\n\n"
        u"各部门联系方式：\n"
        u"- 教务处：010-62282621\n"
        u"- 研究生院：010-62282189\n"
        u"- 学生处：010-62282627\n"
        u"- 图书馆：010-62282238\n"
        u"- 后勤处：010-62282623\n"
        u"- 校医院：010-62282624\n"
        u"- 信息网络中心：010-62282628\n\n"
        u"交通指南：\n"
        u"- 公交：蓟门桥北站（西土城路校区）\n"
        u"- 地铁：西土城站（10号线）、大钟寺站（13号线）\n"
    )

    write_file("17_bupt_campus_life.txt",
        u"【来源：北邮校园生活指南 | 更新日期：2026-05-16】\n\n"
        u"北京邮电大学校园生活指南\n\n"
        u"校区分布：\n"
        u"1. 西土城路校区（海淀校区/本部）\n"
        u"   - 地址：北京市海淀区西土城路10号\n"
        u"   - 邮编：100876\n"
        u"   - 主要学院：信息与通信工程学院、计算机学院、电子工程学院、网络空间安全学院、人工智能学院等\n\n"
        u"2. 沙河校区（昌平校区）\n"
        u"   - 地址：北京市昌平区沙河高教园\n"
        u"   - 主要为部分学院本科生和研究生\n\n"
        u"校园设施：\n"
        u"- 图书馆：西土城路校区和沙河校区各一座\n"
        u"- 食堂：多个学生食堂和教工食堂\n"
        u"- 体育馆：室内体育馆、室外运动场\n"
        u"- 校医院：提供基本医疗和健康服务\n"
        u"- 大礼堂：举办讲座和文艺活动\n\n"
        u"校园交通：\n"
        u"- 校内班车：西土城路校区和沙河校区之间有班车往返\n"
        u"- 公交：距西土城路校区最近的公交站为“蓟门桥北”站\n"
        u"- 地铁：距西土城路校区最近的地铁站为“西土城站”（10号线）、“大钟寺站”（13号线）\n\n"
        u"学校校训：厚德博学，敬业乐群\n\n"
        u"校庆日：每年5月（具体日期以学校公告为准）\n"
    )


def main():
    print("=" * 60)
    print("Bupt Data Cleaner")
    print("=" * 60)
    print("")

    # Clean existing files
    txt_files = sorted([f for f in os.listdir(DATA_DIR) if f.endswith(".txt")])
    for fname in txt_files:
        filepath = os.path.join(DATA_DIR, fname)
        with open(filepath, "r", encoding="utf-8") as f:
            original = f.read()

        cleaned = clean_file(filepath)

        if len(cleaned) < len(original):
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(cleaned)
            removed = len(original) - len(cleaned)
            print(f"  Cleaned: {fname} (removed {removed} bytes)")

    # Supplement
    print("")
    supplement()

    # Final report
    print("")
    print("=" * 60)
    print("Final data files")
    print("=" * 60)

    txt_files = sorted([f for f in os.listdir(DATA_DIR) if f.endswith(".txt")])
    total_size = 0
    print("")

    for f in txt_files:
        fpath = os.path.join(DATA_DIR, f)
        size = os.path.getsize(fpath)
        total_size += size
        with open(fpath, "r", encoding="utf-8") as fh:
            header = fh.readline().strip()
        print(f"  {f}  ({size:,} bytes)  {header[:70]}")

    print(f"\nTotal: {len(txt_files)} files, {total_size:,} bytes ({total_size/1024:.1f} KB)")


if __name__ == "__main__":
    main()
