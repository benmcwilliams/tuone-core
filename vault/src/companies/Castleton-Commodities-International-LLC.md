```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Castleton-Commodities-International-LLC" or company = "Castleton Commodities International LLC")
sort location, dt_announce desc
```
