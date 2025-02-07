```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "PowerHouse-Energy-Group-plc" or company = "PowerHouse Energy Group plc")
sort location, dt_announce desc
```
