```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Platina-Partners" or company = "Platina Partners")
sort location, dt_announce desc
```
