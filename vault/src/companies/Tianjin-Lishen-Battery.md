```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Tianjin-Lishen-Battery" or company = "Tianjin Lishen Battery")
sort location, dt_announce desc
```
