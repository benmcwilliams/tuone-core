```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Sizewell-C" or company = "Sizewell C")
sort location, dt_announce desc
```
