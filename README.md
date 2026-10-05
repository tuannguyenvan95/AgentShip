# ⚓ AgentShip: Global Maritime Demurrage & Weather Risk Court

> **Track:** Supply Chain / Real World Assets (RWA) / TradeFi / Maritime Law  
> **Target Network:** GenLayer StudioNet (Chain ID: `61999` / Hex: `0xF22F`, RPC: `https://studio.genlayer.com/api`)  
> **Deployed Intelligent Contract (v3.0):** [`0x133f95019925c8fAC02BE0bD1b86F947AA50F13F`](https://studio.genlayer.com)  
> **GitHub Repository:** [https://github.com/tuannguyenvan95/AgentShip](https://github.com/tuannguyenvan95/AgentShip)  
> **Live Production dApp:** [https://frontend-three-drab-v46xpao16q.vercel.app](https://frontend-three-drab-v46xpao16q.vercel.app) (Mirror: [https://frontend-2cd2gr7xl-tynamy.vercel.app](https://frontend-2cd2gr7xl-tynamy.vercel.app))  

---

## 🌊 1. Bối cảnh & Bài toán nghiệp vụ

Tranh chấp phí lưu bãi/lưu tàu (**Demurrage & Detention**) trong ngành vận tải biển quốc tế trị giá hàng tỷ USD mỗi năm giữa **Chủ hàng** (*Charterer / Shipper*) và **Hãng tàu** (*Carrier / Shipowner*).

### Vấn đề thực tế:
- Khi tàu đến cảng đích muộn hoặc dỡ hàng chậm hơn khung thời gian thỏa thuận (**Laytime**), hãng tàu phạt chủ hàng phí Demurrage rất nặng.
- Ngược lại, chủ hàng từ chối trả tiền với lý do thời tiết cực đoan (bão biển, sóng cấp 8+, sương mù dày) thuộc diện **Bất khả kháng** (*Force Majeure*).
- Smart contract truyền thống trên EVM (Solidity) **không thể đọc hiểu dữ liệu định vị hàng hải** (*AIS tracking logs*) hay đối chiếu trạm khí tượng đại dương (*NOAA / ECMWF*).

### Giải pháp đột phá từ AgentShip trên GenLayer:
1. **Ký quỹ hợp đồng thuê tàu (`create_voyage_escrow`)**: Chủ hàng nạp cước tàu (*Base Freight*) và khoản cọc bảo chứng lưu tàu (*Demurrage Buffer*) vào escrow.
2. **Hãng tàu nộp bằng chứng hành trình (`submit_voyage_logs`)**: Cung cấp link định vị AIS (tọa độ, vận tốc knot, thời gian neo đậu) và link trạm khí tượng đại dương.
3. **Tòa trọng tài hàng hải AI on-chain (`adjudicate_demurrage`)**:
   - Cào dữ liệu hành trình và thời tiết qua `gl.nondet.web.render`.
   - Đối chiếu tốc độ hải trình, hướng gió Beaufort, chiều cao sóng thực tế dọc tuyến đường biển qua GenVM Subjective Consensus.
   - **Phán quyết tự động**:
     - `FORCE_MAJEURE_EXCUSED`: Chậm trễ do bão biển thật sự (sóng $\ge 6m$) $\rightarrow$ Miễn phạt Demurrage, hoàn cọc buffer cho chủ hàng, thanh toán cước cho hãng tàu.
     - `DEMURRAGE_ENFORCED`: Thời tiết bình thường nhưng tàu/cảng dỡ hàng chậm $\rightarrow$ Khấu trừ tiền phạt chuyển cho hãng tàu.
     - `CLEAN_ON_TIME`: Tàu hoàn thành đúng hạn $\rightarrow$ Thanh toán cước đầy đủ cho hãng tàu.

---

## 🚀 2. Nâng cấp Milestone Đột Phá (v1 $\rightarrow$ v2 $\rightarrow$ v3)

| Phiên bản | Tính năng then chốt & Bảo vệ mật mã | Đảm bảo hệ thống |
| :--- | :--- | :--- |
| **Milestone v1** | - **Canary Token Defense** (`CANARY_AGENT_SHIP_MARITIME_V1`).<br>- Multi-source web rendering (AIS + NOAA).<br>- SHA-256 combined telemetry hash pinning. | Chống prompt injection tuyệt đối, đảm bảo tính tất định của đồng thuận validator. |
| **Milestone v2** | - **Stake-Based Judicial Appeal Court**: Yêu cầu cọc 10% Dispute Bond.<br>- Thắng kháng cáo: Hoàn 100% bond. Thua: Bị slash chuyển cho đối phương.<br>- **24-block Cooling-off Window** trước khi giải ngân.<br>- Zero admin backdoor. | Chống griefing attack và spam khiếu nại vô cớ, bảo toàn tài chính không có cửa rút lén. |
| **Milestone v3** | - **On-Chain Maritime Reputation Engine**: Chấm điểm tín nhiệm và phân hạng (Bronze, Silver, Gold, Platinum).<br>- **Dynamic Fast-Track Adjudication**: Đối tác đạt Gold/Platinum được rút ngắn cooling-off xuống **12 blocks**.<br>- **Cargo Syndicate Co-Funding Pool**: Cho phép nhiều chủ hàng đồng ký quỹ và hoàn trả theo tỷ lệ (Proportional Clawback) khi hủy đơn. | Mở rộng quy mô cho logistics quốc tế nhiều bên tham gia, tối ưu hóa tốc độ giải ngân cho đối tác uy tín. |

---

## 🏛️ 3. Kiến trúc Smart Contract (`contracts/contract.py`)

- **Magic Pragma:** `# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }`
- **GenVM Storage Types:** `TreeMap[u64, MaritimeVoyage]`, `DynArray[u64]`, `TreeMap[str, bigint]`, `TreeMap[str, u32]`.
- **Native Transfers:** `gl.get_contract_at(recipient).emit_transfer(value=u256(int(amount)))`.
- **Hệ thống hàm chính:**
  - `create_voyage_escrow`: Khởi tạo ký quỹ thuê tàu.
  - `pledge_voyage_escrow`: Đồng ký quỹ nghiệp đoàn hàng hải (Milestone v3).
  - `submit_voyage_logs`: Hãng tàu nhận chuyến và liên kết telemetry.
  - `adjudicate_demurrage`: Bồi thẩm đoàn AI phân xử lưu bãi & bão biển.
  - `appeal_verdict`: Kháng cáo với 10% cọc bond trong cửa sổ cooling-off.
  - `adjudicate_appeal`: Tòa phúc thẩm tối cao GenLayer phân xử lại.
  - `finalize_settlement`: Rút tiền sau khi hết hạn cooling-off (12 hoặc 24 blocks).
  - `cancel_or_reclaim`: Hoàn cọc theo tỷ lệ nếu không ai nhận đơn hoặc bị bỏ rơi.

---

## 🧪 4. Kiểm Thử Tự Động (`tests/test_agentship.py`)

Tất cả 9 bài test được kiểm thử tự động và vượt qua **100%**:
- `test_contract_syntax_and_structure`: Kiểm tra cú pháp GenVM.
- `test_voyage_struct_attributes`: Kiểm tra trường dữ liệu storage.
- `test_agentship_force_majeure_weather_excuse`: Phán quyết bão sóng $\ge 6m$ miễn phạt.
- `test_agentship_unexcused_demurrage_enforced`: Phạt lưu bãi khi chậm trễ vô cớ.
- `test_agentship_clean_on_time_delivery`: Giao hàng đúng hạn.
- `test_agentship_appeal_upheld_and_bond_returned`: Kháng cáo thành công hoàn bond.
- `test_agentship_appeal_dismissed_and_bond_slashed`: Kháng cáo thất bại bị phạt bond.
- `test_agentship_v3_syndicate_pooling_and_proportional_refund`: Đồng ký quỹ và hoàn tiền theo tỷ lệ.
- `test_agentship_v3_reputation_tiers_and_leaderboard`: Chấm điểm uy tín và bảng xếp hạng.

Chạy kiểm thử:
```bash
pytest -v
```

---

## 💻 5. Hướng Dẫn Cài Đặt & Chạy Ứng Dụng

### Khởi chạy Frontend:
```bash
cd frontend
npm install
npm run dev
```

### Triển khai Contract lên StudioNet:
```bash
python scripts/deploy_to_studionet.py
python scripts/seed_studionet_voyages.py
```
