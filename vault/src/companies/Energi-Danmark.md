```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Energi-Danmark" or company = "Energi Danmark")
sort location, dt_announce desc
```
