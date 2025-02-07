```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "PPC-Renewables-SA" or company = "PPC Renewables SA")
sort location, dt_announce desc
```
