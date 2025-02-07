```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Wageningen-University-&-Research" or company = "Wageningen University & Research")
sort location, dt_announce desc
```
