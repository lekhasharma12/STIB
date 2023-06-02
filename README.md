# Spill the Implicit Beans : Interpreting figurative texts using prompting
_This project was done as part of a major course requirement for the Advanced NLP course by Mohit Iyyer at UMass Amherst Spring 2023_
"Spill the implicit beans" or STIB is a project to leverage different prompting strategies to get better literal translations for figurative language texts, specifically Metaphor, Idiom, Simile and Sarcasm sentences.

We use zero-shot prompting as our baseline and then test few-shot prompting, instruction prompting and chain of thought prompting to compare performances across these strategies. We also classify these figurative sentences and add the type in these prompts to check if knowing the type of figurative sentence helps to generate better literal translations.

Our Dataset folder consists of train and test data for both Classification and Prompting.

Our Code folder is also divided into Classification and Prompting folders and each of them consists of separate code files for each strategy of classification and prompting clearly specified by the file name. Please see [this report](https://drive.google.com/file/d/1HPDcTsoQWwl3CrgUD6COQzNCWvbb7_Hn/view?usp=sharing) for a more detailed analysis.
