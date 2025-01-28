```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Offshore-Design-Engineering" or company = "Offshore Design Engineering")
sort location, dt_announce desc
```
