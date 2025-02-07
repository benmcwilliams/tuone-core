```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Sapienza-University-of-Rome" or company = "Sapienza University of Rome")
sort location, dt_announce desc
```
