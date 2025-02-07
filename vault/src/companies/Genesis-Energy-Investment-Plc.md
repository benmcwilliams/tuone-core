```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Genesis-Energy-Investment-Plc" or company = "Genesis Energy Investment Plc")
sort location, dt_announce desc
```
