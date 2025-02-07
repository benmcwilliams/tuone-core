```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Geothermal-Engineering" or company = "Geothermal Engineering")
sort location, dt_announce desc
```
