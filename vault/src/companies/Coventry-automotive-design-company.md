```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Coventry-automotive-design-company" or company = "Coventry automotive design company")
sort location, dt_announce desc
```
