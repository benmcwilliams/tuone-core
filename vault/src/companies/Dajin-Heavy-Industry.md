```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Dajin-Heavy-Industry" or company = "Dajin Heavy Industry")
sort location, dt_announce desc
```
