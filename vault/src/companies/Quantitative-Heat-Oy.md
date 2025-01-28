```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Quantitative-Heat-Oy" or company = "Quantitative Heat Oy")
sort location, dt_announce desc
```
