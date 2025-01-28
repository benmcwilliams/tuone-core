```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Brighton-Energy-Cooperative" or company = "Brighton Energy Cooperative")
sort location, dt_announce desc
```
