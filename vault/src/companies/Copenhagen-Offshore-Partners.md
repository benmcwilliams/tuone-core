```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Copenhagen-Offshore-Partners" or company = "Copenhagen Offshore Partners")
sort location, dt_announce desc
```
